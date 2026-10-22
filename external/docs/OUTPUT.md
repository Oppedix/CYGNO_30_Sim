# External compact/raw contract and normalization

The table shapes and units from [shared OUTPUT](../../docs/OUTPUT.md) are reused.
Internal output retains its existing convention. External `RunMetadata.SourcePolicy`
is `environmental-surface-v1`; `OutputMetadata.CompactProcessingVersion` is
`external-track-volumes-v1`. Schema version stays 1 because branch layouts do
not change. An internal reader rejects this processing convention by default.

## External semantic change

There is **one Group per event-local track entering sensitive gas**, for all
particle species, including neutrons, gamma, recoil ions, protons and zero-deposit
steps. GroupIndex follows first sensitive encounter; each Group contains exactly
one track. Track deposits add per gas volume in encounter order, even if a track
is resumed after another one. First coordinates/time are the first step in that
track/volume, including a zero-deposit first touch. `TrackGroups` has exactly one
link per stored track. `Nucleus` is empty in external and never used for selection.
Neutral local energy deposits are retained in the `other` channel, not discarded.

The event-local accumulator buffers one event, not the run. First positions are
not full track trajectories. Independent primary events have no absolute time
relation. Captures/secondary deposits within a Geant4 event are included without
a readout time gate; long-lived activation is not a detector exposure model.

`SimulationMetadata` is a one-row external-only tree:

| Field | Type / meaning |
|---|---|
| Mode | string `external` |
| Shielding | string `none` or `copper20` |
| PhysicsList | string `QGSP_BIC_HP_EMZ` (RDM also registered) |
| SourceHash | SHA256 of compiled source inputs |
| ExternalGeometryHash | SHA256 of shared `common/ExternalGeometry.hh` |
| SourceRadius_mm | double, actual enclosing source radius |

`GeometryHash` still identifies the unmodified common detector dimensions.
The **full external identity** additionally requires shielding selection, external
geometry hash, source radius, source hash, physics/data environment and saved
spectrum/config. Never identify a shielded setup by `GeometryHash` alone.

## Primary-event analysis

For each EventNumber, sum `EnergyDeposit * 1000` in GroupIndex/VolumeOrder order.
Add every volume's contribution to `total` and its particle channel. The channels
are `electromagnetic` (e-/e+), `charged_hadron` (p,d,t,alpha,He3 and named ions),
and `other` (including neutral local deposits). No quenching is applied.
Count an event once per channel only if that channel has **positive energy**.
An event can appear in multiple channel spectra; they must not be added as if
they partitioned the number of detected primary events. Their energy sums do
partition the total deposited energy, up to floating-point roundoff.

There are 1000 uniform 1-keV bins in [0,1000), plus explicit under/overflow.
E=1000 keV is overflow. The unbinned window is 10<E<=400 keV. Missing events and
zero-only events contribute no histogram entries but **remain in generated N**.
MC variance is Poisson primary-event counts times the square of the annual scale;
flux, spectral, mechanical and response uncertainties are not included. A zero
observed bin has zero displayed MC error, not a zero physical upper limit.

## Flux convention

Let S=4π(R_mm/10)² in cm², T=365×24×3600 seconds, and N be the actual complete
`RunAccounting.GeneratedPrimaries` (not sensitive events, stored groups or tracks).

- `inward_current`: incident rate = Φ × S; scale = Φ × S × T / N.
- `scalar`: for an isotropic field, inward current = Φ/4; scale = Φ × S × T / (4N).

Lambert incidence has p(μ)=2μ, μ=-direction·outward_normal in [0,1]. It describes
crossings from an isotropic radiation field; uniform solid-angle directions on a
surface are a different distribution. No focusing to the detector or rejection
of primary misses is used. GPS User histogram values are **bin probabilities**;
the first point is the lower edge and has zero weight. Source densities must be
integrated over bin widths and normalized before use, especially for unequal bins.
The integrated flux applies exactly to the simulated energy support.

C++ reads only Groups/GroupVolumes and small metadata, with finite values,
ordering, gas-ID and primary-accounting checks. It trusts the completed runner
campaign for checksums and unused track tables. Python checks those artifacts and
all compact relationships; use it for the full audit or both-mode parity.
Both analyzers create a new `.partial` directory and rename after success.
They reject existing outputs and outputs inside the campaign.
