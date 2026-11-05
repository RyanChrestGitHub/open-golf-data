# Product direction

Open Golf Data aims to make launch-monitor outputs portable through an open,
inspectable contract. Golfers should be able to use their lawfully accessible
records in compatible tools. Makers should be able to support that contract
without disclosing their proprietary measurement technology.

## Build the proof in order

1. Establish the source, permitted use and provenance of a reproducible example.
2. Preserve its original bytes and document a loss-aware mapping into the model.
3. Have a separate consumer use that model without depending on the source format.
4. Repeat with a second source and show what the consumer can reuse unchanged.
5. Specify and validate live-event capabilities only where authorized evidence
   supports them. File import alone does not establish readiness, device control
   or a live simulator connection.
6. Demonstrate repeatable delivery to the correct consenting golfer.

These are product acceptance goals, not completed milestones or authority to
collect data, connect equipment, publish records or change security policy.

## Make the model useful without hiding uncertainty

Preserve source field names, units, versions and unknown fields. Keep a reference
to original bytes and make transformations inspectable. Unknown or unavailable
values remain missing; estimates and simulations retain their meaning. Record
what a source actually supports rather than inventing a universal minimum that
silently changes its data.

A research dataset can reveal useful fields. A hand-written protocol fixture can
exercise structure. A native export can support a source mapping. Each needs its
own provenance and allowed-use assessment; none alone establishes device accuracy,
physical compatibility, golfer identity or adoption.

## Earn adoption with useful evidence

For golfers, demonstrate portable records and control over permitted sharing.
For monitor makers, demonstrate a faithful mapping from supported outputs.
For simulator and app makers, demonstrate a reusable consumer and explicit
capability boundaries. Easier development and adoption remain hypotheses until
independent use provides evidence.

“Any launch monitor, any simulator, your data” describes the ambition. Public
support claims must name the tested interface, version, evidence and limitations.
Applicable source terms, privacy, access and participant rights need individual
assessment; the slogan is not a blanket legal ownership conclusion.

The current repository provides a synthetic ledger/export demonstration and
local evidence tools. It does not yet prove real hardware support, an adopted
cross-vendor standard, live integration or authenticated golfer delivery.
Existing [agent instructions](../AGENTS.md) and [security policy](SECURITY.md)
continue to govern implementation and review.
