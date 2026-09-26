// Standalone Samuele ER analysis of a completed, unpacked compact campaign.
// From the repository root (ROOT built with RooFit/HS3 JSON support):
//   g++ -O3 -std=c++17 -ffp-contract=off analysis/common_c++/AnalyzeCompactCampaign.cpp \
//       -I. $(root-config --cflags --libs) -lRooFitHS3 \
//       -o analysis/common_c++/AnalyzeCompactCampaign
//   analysis/common_c++/AnalyzeCompactCampaign CAMPAIGN_DIR NEW_OUTPUT_DIR
// Do not use -ffast-math: the order of floating-point operations is scientific input.
// ROOT's own JSON reader avoids an external JSON dependency. No Geant4 is needed.

#include <RooFit/Detail/JSONInterface.h>
#include <TCanvas.h>
#include <TColor.h>
#include <TFile.h>
#include <TH1D.h>
#include <THStack.h>
#include <TLeaf.h>
#include <TLeafC.h>
#include <TLegend.h>
#include <TNamed.h>
#include <TObjString.h>
#include <TPaveText.h>
#include <TROOT.h>
#include <TStyle.h>
#include <TTree.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <map>
#include <memory>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

#ifdef __FAST_MATH__
#error "Fast math changes the canonical summation semantics; compile without it."
#endif

namespace fs = std::filesystem;
using RooFit::Detail::JSONNode;
using RooFit::Detail::JSONTree;
constexpr int bins = 900;
constexpr double maximumEnergy = 2000.;
constexpr double binWidth = maximumEnergy / bins;
// Presentation order only; physical contribution membership comes from matrix.json.
const std::array<std::string, 7> categories = {
    "Camera Lenses", "Vessel", "Camera Sensors", "Cathodes", "Resistors", "GEMs", "Field Cage"};
const std::array<const char*, 6> windows = {
    "all", "gt10", "gt10_le400", "underflow", "in_range", "overflow"};
const std::array<const char*, 2> selections = {"no_cut", "fiducial_20mm"};

// Small file/ROOT operations live here; the complete analysis follows in main.
void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}
std::string readText(const fs::path& path) {
    std::ifstream input(path);
    require(bool(input), "Cannot read " + path.string());
    std::ostringstream text;
    text << input.rdbuf();
    require(!input.bad(), "Read failed: " + path.string());
    return text.str();
}
std::unique_ptr<JSONTree> readJson(const fs::path& path) {
    try { return JSONTree::create(readText(path)); }
    catch (const std::exception& error) {
        throw std::runtime_error(path.string() + ": " + error.what());
    }
}
std::string jsonText(const JSONNode& node) {
    std::ostringstream text;
    node.writeJSON(text);
    return text.str();
}
double number(const JSONNode& node) {
    require(node.is_number(), "Expected JSON number: " + node.key());
    const double value = node.val_double();
    require(std::isfinite(value), "Nonfinite number: " + node.key());
    return value;
}
int integer(const JSONNode& node) {
    const double value = number(node);
    require(value >= 0 && value <= std::numeric_limits<int>::max() && value == std::floor(value),
            "Invalid nonnegative int32: " + node.key());
    return static_cast<int>(value);
}
bool within(const fs::path& path, const fs::path& parent) {
    auto relative = path.lexically_relative(parent);
    return !relative.empty() && *relative.begin() != "..";
}
fs::path inside(const fs::path& parent, const std::string& name) {
    const fs::path relative(name);
    require(!name.empty() && !relative.is_absolute() && name.find('\\') == std::string::npos,
            "Invalid campaign-relative path: " + name);
    for (const auto& part : relative) require(part != "..", "Parent traversal in " + name);
    const auto path = fs::canonical(parent / relative);
    require(within(path, fs::canonical(parent)), "Path escapes campaign: " + name);
    return path;
}
TTree& tree(TFile& file, const char* name, bool oneRow = false) {
    auto* result = dynamic_cast<TTree*>(file.Get(name));
    require(result && (!oneRow || result->GetEntries() == 1), std::string("Missing/invalid tree: ") + name);
    // Disable everything, then activate only the branches actually used below.
    result->SetBranchStatus("*", false);
    return *result;
}
TLeaf* branch(TTree& tree, const char* name, const char* type, void* address = nullptr) {
    auto* leaf = tree.GetLeaf(name);
    require(leaf && std::string(leaf->GetTypeName()) == type && !leaf->GetLeafCount() &&
            (std::string(type) == "Char_t" || leaf->GetLenStatic() == 1),
            std::string("Missing/wrong branch: ") + tree.GetName() + "." + name);
    tree.SetBranchStatus(name, true);
    if (address) require(tree.SetBranchAddress(name, address) >= 0, std::string("Cannot bind ") + name);
    return leaf;
}
std::string stringField(TTree& tree, const char* name) {
    auto* leaf = branch(tree, name, "Char_t");
    require(tree.GetEntry(0) > 0, "Cannot read metadata row");
    // Geant4 writes ROOT character leaves, not std::string object branches.
    // ROOT owns the string buffer; no fixed-size character array is needed.
    return static_cast<TLeafC*>(leaf)->GetValueString();
}
std::unique_ptr<TH1D> histogram(const std::string& name) {
    auto result = std::make_unique<TH1D>(name.c_str(), name.c_str(), bins, 0., maximumEnergy);
    // TH1D is a double-precision histogram. Detach it from the current TFile so
    // closing an input file cannot delete a histogram we still need.
    result->SetDirectory(nullptr);
    return result;
}
int histogramBin(double energy) {
    if (energy < 0.) return 0;
    if (energy >= maximumEnergy) return bins + 1;
    // Exactly analysis/common/spectra.py (ROOT 6.40 uniform-edge corrections).
    // Explicit indexing also preserves this convention on older ROOT releases.
    const int approximate = static_cast<int>(energy / binWidth);
    return 1 + approximate - (energy < binWidth * approximate)
           + (binWidth * (approximate + 1) <= energy);
}

// One small record per contribution, never one C++ object per group/step.
struct Contribution {
    std::string id, category, unit, path;
    double activity = 0., quantity = 0., scale = 0.;
    int generated = 0;
    Long64_t processed = 0;
    std::array<std::array<Long64_t, 6>, 2> counts{};
    std::array<std::unique_ptr<TH1D>, 2> raw;
};

int main(int argc, char** argv) try {
    require(argc == 3, "Usage: AnalyzeCompactCampaign CAMPAIGN_DIR NEW_OUTPUT_DIR");
    gROOT->SetBatch(true); // Save plots without opening a graphical desktop window.
    gStyle->SetOptStat(0);

    // ------------------------------------------------------------
    // 1. Read the campaign
    // ------------------------------------------------------------
    const fs::path campaignPath = fs::canonical(argv[1]);
    const fs::path outputPath = fs::weakly_canonical(fs::absolute(argv[2]));
    require(fs::is_directory(campaignPath), "Input must be an unpacked campaign directory");
    require(!fs::exists(outputPath) && !within(outputPath, campaignPath),
            "Output must be a NEW directory outside the simulation campaign");
    const auto campaignDocument = readJson(campaignPath / "campaign.json");
    const auto configDocument = readJson(campaignPath / "config.json");
    const auto matrixDocument = readJson(campaignPath / "matrix.json");
    const auto geometryDocument = readJson(campaignPath / "geometry.json");
    const JSONNode& campaign = campaignDocument->rootnode();
    const JSONNode& config = configDocument->rootnode();
    const JSONNode& matrix = matrixDocument->rootnode();
    const JSONNode& geometry = geometryDocument->rootnode();
    const auto& environment = campaign["identity"]["effective_environment"];
    require(integer(campaign["schema_version"]) == 3 && campaign["stage"].val() == "simulation" &&
            campaign["status"].val() == "complete" && campaign["coverage"].val() == "26/26",
            "Expected a completed schema-3, 26-contribution simulation campaign");
    require(config["output_mode"].val() == "compact" && integer(config["output_schema_version"]) == 1,
            "This analysis requires output_mode=compact, schema 1");
    require(jsonText(config) == jsonText(campaign["identity"]["config"]) &&
            jsonText(matrix) == jsonText(campaign["identity"]["matrix"]), "Campaign snapshot disagreement");
    const std::string layout = config["layout"].val();
    const std::string model = config["model"].val();
    const std::string policy = config["source_policy"].val();
    const std::string geometryHash = environment["geometry_hash"].val();
    require(model == "code-compatible" && policy == "historical", "Unsupported model/source policy");
    require(geometry["layout"].val() == layout && geometry["geometry_hash"].val() == geometryHash &&
            geometry["source_hash"].val() == environment["source_hash"].val(), "Geometry snapshot mismatch");
    require(integer(matrix["schema_version"]) == 1 && matrix["matrix_id"].val() == "thesis-table7.1-v1" &&
            integer(matrix["seconds_per_year"]) == 31536000 &&
            matrix["quantity_policy"].val() == "constructed-component-mass-kg-or-placement-count",
            "Unsupported matrix/year/quantity convention");
    const auto& rows = matrix["contributions"];
    require(rows.is_seq() && rows.num_children() == 26 && campaign["job_records"].num_children() == 26,
            "Expected all 26 matrix contributions and job records");

    // ------------------------------------------------------------
    // 2. Read constructed quantities and contribution information
    // ------------------------------------------------------------
    // This export comes from the actual constructed geometry. Read columns by
    // name; masses and resistor piece counts are never compiled into this code.
    std::map<std::string, std::array<double, 2>> quantities;
    std::map<std::string, std::string> quantityHeaders;
    std::map<std::string, size_t> columns;
    std::istringstream quantityInput(readText(campaignPath / "quantities.tsv"));
    std::string line;
    while (std::getline(quantityInput, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.empty()) continue;
        if (line.rfind("# ", 0) == 0) {
            const auto colon = line.find(':');
            require(colon != std::string::npos, "Invalid quantity metadata");
            const auto start = line.find_first_not_of(" \t", colon + 1);
            require(start != std::string::npos && quantityHeaders.emplace(
                line.substr(2, colon - 2), line.substr(start)).second, "Invalid/duplicate quantity header");
            continue;
        }
        std::vector<std::string> fields;
        std::istringstream input(line);
        std::string field;
        while (std::getline(input, field, '\t')) fields.push_back(field);
        if (columns.empty()) {
            for (size_t i = 0; i < fields.size(); ++i)
                require(columns.emplace(fields[i], i).second, "Duplicate quantity column");
            continue;
        }
        require(fields.size() == columns.size(), "Malformed quantity row");
        const auto component = fields.at(columns.at("component"));
        size_t usedMass = 0, usedPieces = 0;
        const auto& massText = fields.at(columns.at("mass_kg"));
        const auto& piecesText = fields.at(columns.at("pieces"));
        const double mass = std::stod(massText, &usedMass);
        const double pieces = std::stod(piecesText, &usedPieces);
        require(usedMass == massText.size() && usedPieces == piecesText.size() &&
                std::isfinite(mass) && mass > 0. && std::isfinite(pieces) && pieces > 0. &&
                pieces == std::floor(pieces), "Invalid constructed quantities: " + component);
        require(quantities.emplace(component, std::array<double, 2>{mass, pieces}).second,
                "Duplicate constructed component");
        const auto& saved = campaign["quantities"][component];
        require(mass == number(saved["mass_kg"]) && pieces == number(saved["pieces"]) &&
                fields.at(columns.at("geometry_material")) == saved["geometry_material"].val(),
                "Constructed quantities disagree with campaign: " + component);
    }
    require(quantityHeaders.at("layout") == layout && quantityHeaders.at("detector-model") == model &&
            quantityHeaders.at("source-policy") == policy && quantityHeaders.at("geometry-hash") == geometryHash &&
            quantityHeaders.at("compiled-source-hash") == environment["source_hash"].val() &&
            !quantityHeaders.at("provenance").empty() && quantities.size() == campaign["quantities"].num_children(),
            "Quantity export identity mismatch");

    // geometry.json is the runner's export of common/DetectorGeometry.hh.
    // Use its gas sizes and centers directly, without a second coordinate table
    // or a dependency on today's local geometry header/build/Geant4 installation.
    std::array<double, 3> gasSize{};
    require(geometry["gas_size_mm"].num_children() == 3, "Invalid gas dimensions");
    for (int axis = 0; axis < 3; ++axis) {
        gasSize[axis] = number(geometry["gas_size_mm"].child(axis));
        require(gasSize[axis] > 40., "Gas dimensions must exceed the two 20 mm insets");
    }
    const auto& centers = geometry["gas_centers_mm"];
    require(centers.is_map() && centers.num_children() > 0, "Missing gas centers");
    std::vector<std::array<double, 3>> gasCenters(centers.num_children());
    for (size_t volume = 0; volume < gasCenters.size(); ++volume) {
        const auto& center = centers[std::to_string(volume)];
        require(center.num_children() == 3, "Invalid gas center");
        for (int axis = 0; axis < 3; ++axis) gasCenters[volume][axis] = number(center.child(axis));
    }

    // The only persistent analysis data are 26 pairs of 902-bin histograms and
    // their exact counters. ROOT streams the large event trees through its cache.
    std::vector<Contribution> results;
    std::set<std::string> contributionIds, categoryNames;
    std::map<std::string, std::string> componentCategories, componentUnits;

    // ------------------------------------------------------------
    // 3. Loop over the 26 compact ROOT files
    // ------------------------------------------------------------
    for (const auto& row : rows.children()) {
        Contribution result;
        result.id = row["id"].val();
        const std::string component = row["component"].val();
        result.category = row["category"].val();
        result.unit = row["activity_unit"].val();
        require(!result.id.empty() && result.id.find_first_not_of(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-") == std::string::npos &&
            contributionIds.insert(result.id).second, "Invalid/duplicate contribution ID");
        require(std::find(categories.begin(), categories.end(), result.category) != categories.end(),
                "Unknown reporting category: " + result.category);
        categoryNames.insert(result.category);
        if (componentCategories.count(component))
            require(componentCategories.at(component) == result.category && componentUnits.at(component) == result.unit,
                    "Inconsistent component category/unit");
        componentCategories[component] = result.category;
        componentUnits[component] = result.unit;
        require(result.unit == "Bq/kg" || result.unit == "Bq/piece", "Unsupported activity unit");
        result.activity = number(row["activity"]);
        result.quantity = quantities.at(component)[result.unit == "Bq/kg" ? 0 : 1];
        require(result.activity > 0., "Activity must be positive");
        const auto directory = inside(campaignPath, "jobs/" + result.id);
        const auto jobDocument = readJson(directory / "manifest.json");
        const JSONNode& job = jobDocument->rootnode();
        require(job["contribution"].val() == result.id && job["status"].val() == "complete" &&
                job["campaign_fingerprint"].val() == campaign["fingerprint"].val() &&
                jsonText(job) == jsonText(campaign["job_records"][result.id]), "Incomplete/mixed job: " + result.id);
        require(integer(job["schema_version"]) == 3 && job["output_mode"].val() == "compact" &&
                integer(job["output_schema_version"]) == 1 && integer(job["workers"]) == 1,
                "Invalid compact job contract: " + result.id);
        const auto attempt = inside(directory, job["attempt"].val());
        const auto attemptDocument = readJson(attempt / "manifest.json");
        require(jsonText(attemptDocument->rootnode()) == jsonText(job), "Active attempt manifest mismatch");
        // Never guess attempt-0001 or select the newest file by filename.
        const auto dataPath = inside(attempt, job["data_path"].val());
        result.path = dataPath.lexically_relative(campaignPath).string();
        std::cout << "[" << results.size() + 1 << "/26] " << result.id << ": " << result.path << std::endl;

        // TFile opens a ROOT container. A TTree is its column-oriented table.
        TFile input(dataPath.c_str(), "READ");
        require(!input.IsZombie() && !input.TestBit(TFile::kRecovered), "Cannot open intact ROOT file: " + result.path);
        auto& metadata = tree(input, "RunMetadata", true);
        require(stringField(metadata, "Layout") == layout && stringField(metadata, "GeometryHash") == geometryHash &&
                stringField(metadata, "DetectorModel") == model && stringField(metadata, "SourcePolicy") == policy,
                "ROOT/campaign scientific identity mismatch: " + result.id);
        auto& outputMetadata = tree(input, "OutputMetadata", true);
        require(stringField(outputMetadata, "OutputFormat") == "compact" &&
                stringField(outputMetadata, "CompactProcessingVersion") == "event-boundaries-and-eof-v2" &&
                stringField(outputMetadata, "TimingDefinition") ==
                    "pre-step global time / ns; Geant4 event-relative, not inter-event time",
                "Unsupported ROOT compact format");
        int schema = 0;
        branch(outputMetadata, "OutputSchemaVersion", "Int_t", &schema);
        require(outputMetadata.GetEntry(0) > 0 && schema == 1, "Unsupported ROOT schema");
        auto& accounting = tree(input, "RunAccounting", true);
        const std::array<const char*, 5> accountingNames = {
            "RunID", "RequestedEvents", "GeneratedPrimaries", "ProcessedEvents", "AbortedEvents"};
        std::array<int, 5> actual{};
        for (size_t i = 0; i < actual.size(); ++i) branch(accounting, accountingNames[i], "Int_t", &actual[i]);
        require(accounting.GetEntry(0) > 0, "Cannot read primary accounting");
        for (size_t i = 0; i < actual.size(); ++i)
            require(actual[i] == integer(job["accounting"][accountingNames[i]]), "ROOT/manifest accounting mismatch");
        result.generated = actual[2];
        require(actual[0] == 0 && actual[1] > 0 && actual[1] == actual[2] && actual[2] == actual[3] && actual[4] == 0 &&
                actual[1] == integer(job["requested_primaries"]) && actual[1] == integer(config["primaries_per_job"]) &&
                actual[2] == integer(job["generated_primaries"]), "Invalid/incomplete generated-primary accounting");

        auto& groups = tree(input, "Groups");
        auto& volumes = tree(input, "GroupVolumes");
        int event = 0, groupIndex = 0, volumeCount = 0;
        branch(groups, "EventNumber", "Int_t", &event);
        branch(groups, "GroupIndex", "Int_t", &groupIndex);
        branch(groups, "VolumeCount", "Int_t", &volumeCount);
        auto* particle = branch(groups, "ParticleName", "Char_t");
        int volumeEvent = 0, volumeGroup = 0, order = 0, volumeNumber = 0;
        double depositedMeV = 0., x = 0., y = 0., z = 0.;
        branch(volumes, "EventNumber", "Int_t", &volumeEvent);
        branch(volumes, "GroupIndex", "Int_t", &volumeGroup);
        branch(volumes, "VolumeOrder", "Int_t", &order);
        branch(volumes, "VolumeNumber", "Int_t", &volumeNumber);
        branch(volumes, "EnergyDeposit", "Double_t", &depositedMeV);
        branch(volumes, "x_first", "Double_t", &x);
        branch(volumes, "y_first", "Double_t", &y);
        branch(volumes, "z_first", "Double_t", &z);
        for (auto* table : {&groups, &volumes}) {
            table->SetCacheSize(16 * 1024 * 1024); // Bounded read-ahead for selected branches.
            for (int i = 0; i < table->GetListOfBranches()->GetEntries(); ++i) {
                const auto* b = table->GetListOfBranches()->At(i);
                if (table->GetBranchStatus(b->GetName())) table->AddBranchToCache(b->GetName(), true);
            }
            table->StopCacheLearningPhase();
        }
        for (int cut = 0; cut < 2; ++cut) result.raw[cut] = histogram(result.id + "_" + selections[cut]);
        const Long64_t volumeEntries = volumes.GetEntries();
        Long64_t nextVolume = 0;
        int previousEvent = -1, previousGroup = -1;
        // A fixed, tiny stamp array checks duplicate gas copies without allocating
        // a container for every group. Tracks/TrackGroups are never opened.
        std::vector<Long64_t> seenGas(gasCenters.size(), -1);
        for (Long64_t entry = 0; entry < groups.GetEntries(); ++entry) {
            // GetEntry reads this row's activated branches into the bound variables.
            require(groups.GetEntry(entry) > 0, "Cannot read Groups entry");
            ++result.processed; // Includes alpha-labeled historical groups.
            require(event >= 0 && event < result.generated && event >= previousEvent &&
                    groupIndex == (event == previousEvent ? previousGroup + 1 : 0), "Invalid group identity/order");
            previousEvent = event;
            previousGroup = groupIndex;
            require(volumeCount > 0 && volumeCount <= static_cast<int>(gasCenters.size()) &&
                    volumeCount <= volumeEntries - nextVolume, "Invalid VolumeCount/volume consumption");
            const char* name = static_cast<TLeafC*>(particle)->GetValueString();
            const bool accepted = std::strcmp(name, "e-") == 0 || std::strcmp(name, "e+") == 0;
            if (!accepted) {
                // Stored groups already implement the historical state machine.
                // Skip their consecutive volume rows; there is nothing to regroup.
                nextVolume += volumeCount;
                continue;
            }

            // ------------------------------------------------------------
            // 4. Reconstruct each stored group energy
            // ------------------------------------------------------------
            double energy = 0.;
            bool fiducial = false;
            for (int v = 0; v < volumeCount; ++v) {
                require(volumes.GetEntry(nextVolume++) > 0, "Cannot read GroupVolumes entry");
                require(volumeEvent == event && volumeGroup == groupIndex && order == v,
                        "GroupVolumes key/order mismatch");
                require(volumeNumber >= 0 && volumeNumber < static_cast<int>(gasCenters.size()), "Invalid gas copy ID");
                require(seenGas[volumeNumber] != entry, "Repeated gas copy within group");
                seenGas[volumeNumber] = entry;
                require(std::isfinite(depositedMeV) && std::isfinite(x) && std::isfinite(y) && std::isfinite(z),
                        "Nonfinite group volume");
                // Multiply EACH MeV deposit before addition, in stored VolumeOrder.
                // No sum-in-MeV-then-convert, reassociation, or fused multiply-add.
                energy += depositedMeV * 1000.;

                // ------------------------------------------------------------
                // 5. Apply the 20 mm fiducial cut
                // ------------------------------------------------------------
                if (v == 0) {
                    const auto& center = gasCenters[volumeNumber];
                    fiducial = std::abs(x - center[0]) <= gasSize[0] / 2. - 20. &&
                               std::abs(y - center[1]) <= gasSize[1] / 2. - 20. &&
                               std::abs(z - center[2]) <= gasSize[2] / 2. - 20.;
                }
            }
            require(std::isfinite(energy), "Nonfinite summed group energy");
            const std::array<bool, 6> flags = {true, energy > 10., energy > 10. && energy <= 400.,
                energy < 0., energy >= 0. && energy < maximumEnergy, energy >= maximumEnergy};
            const int bin = histogramBin(energy);
            for (int cut = 0; cut < (fiducial ? 2 : 1); ++cut) {
                result.raw[cut]->AddBinContent(bin); // Unit count, including ROOT flow bins 0 and 901.
                for (int w = 0; w < 6; ++w) if (flags[w]) ++result.counts[cut][w];
            }
        }
        require(nextVolume == volumeEntries, "Unconsumed/orphan GroupVolumes rows");
        for (int cut = 0; cut < 2; ++cut) {
            result.raw[cut]->ResetStats();
            result.raw[cut]->SetEntries(result.counts[cut][0]);
        }

        // ------------------------------------------------------------
        // 6. Normalize each contribution
        // ------------------------------------------------------------
        // Left-to-right multiplication is identical to common/normalization.py.
        // The denominator is measured accounting, never an assumed run request.
        result.scale = result.activity * result.quantity * 60 * 60 * 24 * 365 / result.generated;
        require(std::isfinite(result.scale), "Nonfinite normalization scale");
        std::cout << "  groups=" << result.processed << ", ER=" << result.counts[0][0]
                  << ", fiducial=" << result.counts[1][0] << ", generated=" << result.generated << std::endl;
        results.push_back(std::move(result));
    }
    require(categoryNames.size() == categories.size(), "Missing reporting category");

    // ------------------------------------------------------------
    // 7. Sum categories and produce the final spectra
    // ------------------------------------------------------------
    std::array<std::array<std::unique_ptr<TH1D>, 7>, 2> categoryHistograms;
    std::array<std::array<std::array<double, bins + 2>, 7>, 2> variances{};
    for (int cut = 0; cut < 2; ++cut)
        for (int c = 0; c < 7; ++c) categoryHistograms[cut][c] = histogram(categories[c]);
    for (const auto& result : results) {
        const int category = std::find(categories.begin(), categories.end(), result.category) - categories.begin();
        for (int cut = 0; cut < 2; ++cut)
            for (int bin = 0; bin <= bins + 1; ++bin) {
                const double count = result.raw[cut]->GetBinContent(bin);
                // Each contribution has its OWN activity/quantity/denominator.
                // Normalize before addition; a category cannot use one common scale.
                categoryHistograms[cut][category]->AddBinContent(bin, count * result.scale);
                variances[cut][category][bin] += count * result.scale * result.scale;
            }
    }

    // Only publish a directory after every input and every output has succeeded.
    // A failure during output leaves an explicitly named .partial directory.
    const fs::path staged = outputPath.string() + ".partial";
    fs::create_directories(outputPath.parent_path());
    require(fs::create_directory(staged), "Staging directory already exists: " + staged.string());
    TFile output((staged / "analysis.root").c_str(), "CREATE");
    require(!output.IsZombie(), "Cannot create analysis.root");
    std::ofstream summary(staged / "summary.txt");
    require(bool(summary), "Cannot create summary.txt");
    summary << std::setprecision(17) << "Campaign: " << campaignPath << "\nLayout: " << layout
            << "\nFingerprint: " << campaign["fingerprint"].val() << "\nCoverage: 26/26\n"
            << "Scale = activity * quantity * 60 * 60 * 24 * 365 / actual generated primaries\n"
            << "Windows: all; E>10; 10<E<=400; E<0; 0<=E<2000; E>=2000 (keV)\n"
            << "Errors: Poisson historical-group counts; no assay/geometry uncertainty.\n"
            << "Trusted completed campaign: no artifact hashing or track relationship validation.\n\n";
    auto* provenance = output.mkdir("provenance");
    provenance->cd();
    TNamed("CampaignPath", campaignPath.c_str()).Write();
    TNamed("Layout", layout.c_str()).Write();
    TNamed("CampaignFingerprint", campaign["fingerprint"].val().c_str()).Write();
    TNamed("ROOTVersion", gROOT->GetVersion()).Write();
    TNamed("HistogramConvention", "900 bins [0,2000); category regular bins counts/keV/year; flows counts/year").Write();
    for (const char* name : {"campaign.json", "config.json", "matrix.json", "geometry.json", "quantities.tsv"})
        TObjString(readText(campaignPath / name).c_str()).Write(name);
    output.cd();

    // Small TTrees preserve exact integer counts independently of binning and
    // weighted rates. The strings below are output object branches owned by us.
    TTree exact("ExactEnergyWindows", "Unbinned contribution counts and annual rates");
    exact.SetDirectory(nullptr);
    std::string id, category, window;
    int cut = 0, generated = 0;
    Long64_t count = 0, processed = 0;
    double rate = 0., variance = 0., scale = 0., activity = 0., quantity = 0.;
    std::string unit, path;
    exact.Branch("Contribution", &id); exact.Branch("Category", &category);
    exact.Branch("Window", &window); exact.Branch("Fiducial", &cut);
    exact.Branch("Count", &count); exact.Branch("RatePerYear", &rate);
    exact.Branch("VariancePerYear2", &variance);
    TTree normalization("Normalization", "Measured denominators and contribution scales");
    normalization.SetDirectory(nullptr);
    normalization.Branch("Contribution", &id); normalization.Branch("Category", &category);
    normalization.Branch("Activity", &activity); normalization.Branch("ActivityUnit", &unit);
    normalization.Branch("Quantity", &quantity); normalization.Branch("GeneratedPrimaries", &generated);
    normalization.Branch("Scale", &scale); normalization.Branch("ProcessedGroups", &processed);
    normalization.Branch("InputPath", &path);
    auto* contributionsDirectory = output.mkdir("contributions");
    std::array<std::array<Long64_t, 6>, 2> totalCounts{};
    std::array<std::array<double, 6>, 2> totalRates{}, totalVariances{};
    for (const auto& result : results) {
        id = result.id; category = result.category; activity = result.activity; unit = result.unit;
        quantity = result.quantity; generated = result.generated; scale = result.scale;
        processed = result.processed; path = result.path;
        normalization.Fill();
        summary << id << " [" << category << "]\n  file=" << path << "\n  activity=" << activity << ' ' << unit
                << " quantity=" << quantity << " generated=" << generated << " scale=" << scale
                << " processed_groups=" << processed << '\n';
        auto* directory = contributionsDirectory->mkdir(id.c_str());
        directory->cd();
        for (cut = 0; cut < 2; ++cut) {
            // Raw histograms make exact equivalence inspectable without dividing
            // normalized floating-point results back by a scale.
            result.raw[cut]->Write((std::string("raw_") + selections[cut]).c_str());
            for (int w = 0; w < 6; ++w) {
                window = windows[w]; count = result.counts[cut][w];
                rate = count * scale; variance = count * scale * scale;
                exact.Fill();
                totalCounts[cut][w] += count;
                totalRates[cut][w] += rate;
                totalVariances[cut][w] += variance;
                summary << "  " << selections[cut] << ' ' << window << ": count=" << count
                        << " rate/year=" << rate << '\n';
            }
        }
    }
    output.cd(); exact.Write(); normalization.Write();
    summary << "\nExact totals (sum individually normalized contributions):\n";
    for (cut = 0; cut < 2; ++cut)
        for (int w = 0; w < 6; ++w)
            summary << selections[cut] << ' ' << windows[w] << ": count=" << totalCounts[cut][w]
                    << " rate/year=" << totalRates[cut][w] << " variance/year^2=" << totalVariances[cut][w] << '\n';

    const std::array<const char*, 7> colors = {
        "#0072B2", "#999999", "#56B4E9", "#E69F00", "#CC79A7", "#D55E00", "#009E73"};
    for (cut = 0; cut < 2; ++cut) {
        auto* directory = output.mkdir(selections[cut]);
        auto* categoryDirectory = directory->mkdir("categories");
        auto total = histogram("total");
        double minimumPositive = std::numeric_limits<double>::infinity();
        for (int c = 0; c < 7; ++c) {
            auto& h = *categoryHistograms[cut][c];
            for (int bin = 0; bin <= bins + 1; ++bin) {
                // Sum in counts/bin/year FIRST, then divide regular bins by the
                // canonical width. Flow bins stay counts/year, as in common.
                const double width = bin >= 1 && bin <= bins ? binWidth : 1.;
                h.SetBinContent(bin, h.GetBinContent(bin) / width);
                h.SetBinError(bin, std::sqrt(variances[cut][c][bin]) / width);
                if (bin >= 1 && bin <= bins && h.GetBinContent(bin) > 0.)
                    minimumPositive = std::min(minimumPositive, h.GetBinContent(bin));
            }
            h.ResetStats();
            h.SetFillColor(TColor::GetColor(colors[c]));
            h.SetLineColor(h.GetFillColor());
            h.GetXaxis()->SetTitle("Deposited energy [keV]");
            h.GetYaxis()->SetTitle("counts / keV / year");
            categoryDirectory->cd(); h.Write();
            total->Add(&h); // Total uses exactly the category spectra drawn below.
        }
        directory->cd(); total->Write();
        const char* figure = cut ? "figure7.6" : "figure7.5";
        const char* title = cut ? "Internal radioactivity: 20 mm fiducial cut" : "Internal radioactivity: no fiducial cut";
        TCanvas canvas(figure, title, 1200, 750);
        canvas.SetLeftMargin(.12); canvas.SetRightMargin(.04); canvas.SetBottomMargin(.12); canvas.SetTopMargin(.14);
        THStack stack("categories", title);
        TLegend legend(.72, .57, .95, .84);
        legend.SetBorderSize(0); legend.SetFillStyle(0); legend.SetTextSize(.028);
        for (int c = 0; c < 7; ++c) {
            stack.Add(categoryHistograms[cut][c].get());
            legend.AddEntry(categoryHistograms[cut][c].get(), categories[c].c_str(), "f");
        }
        const bool nonempty = std::isfinite(minimumPositive);
        canvas.SetLogy(nonempty);
        stack.SetMinimum(nonempty ? minimumPositive * .25 : 0.);
        stack.SetMaximum(nonempty ? total->GetMaximum() * 20. : 1.);
        stack.Draw("HIST");
        stack.GetXaxis()->SetTitle("Deposited energy [keV]");
        stack.GetYaxis()->SetTitle("counts / keV / year");
        stack.GetXaxis()->SetLimits(0., maximumEnergy);
        legend.Draw();
        TPaveText caption(.12, .875, .96, .925, "NDC");
        caption.SetFillStyle(0); caption.SetBorderSize(0); caption.SetTextFont(42); caption.SetTextSize(.022);
        caption.AddText((layout + " | " + config["mode"].val() + " | 26/26 contributions | physics unvalidated").c_str());
        caption.Draw();
        for (const char* extension : {"png", "pdf"}) {
            const auto file = staged / (std::string(figure) + "." + extension);
            canvas.SaveAs(file.c_str());
            require(fs::exists(file) && fs::file_size(file) > 0, "Figure export failed: " + file.string());
        }
    }
    output.Close();
    require(!output.TestBit(TFile::kWriteError), "ROOT output write failure");
    summary << "\nOutputs: analysis.root, figure7.5.png, figure7.5.pdf, figure7.6.png, figure7.6.pdf, summary.txt\nCOMPLETE\n";
    summary.close();
    require(bool(summary), "Summary write failure");
    require(!fs::exists(outputPath), "Output appeared during analysis; refusing overwrite");
    fs::rename(staged, outputPath);
    std::cout << "Complete: " << outputPath << std::endl;
    return 0;
} catch (const std::exception& error) {
    std::cerr << "AnalyzeCompactCampaign: " << error.what() << '\n';
    return 1;
}
