# Data and output schemas

All JSON artifacts use schema_version=1 where a top-level schema is applicable. Exact numbers are serialized as numerator/denominator strings; ordinary measurements are finite JSON numbers. Invalid *evaluation* values become null, with valid counts reported. Inference input nonfinite values are rejected.

## Inference input

`inputs.json` contains `box: {lower:[3], upper:[3]}`, `cameras:[{id,K:[3,3],R:[3,3],t:[3],width,height,undistorted:true}]` and `tracks:[{id,observations:[...]}]`. R,t map world to camera in meters. Each observation has globally unique id, camera_id, uv:[u,v], pixel_radius:[du,dv], positive metric depth, positive half_width, confidence in [0,1], visible=true and depth_convention='optical_z'. IDs are unique across tracks. A track contains at most one observation per camera and at least two observations. No truth/reference fields are consumed.

## Exact system and certificate

`system` includes exact A:[m,3], b:[m], box and m RowTags (track, observation, camera, kind). Point certificates contain kind='point' and point:[3]. Contradictions contain kind='contradiction' and y:[m]. Upper bounds contain kind='upper_bound', c:[3], t, y:[m] and bound. `check_artifact` uses only the standard library and the exact representation; no solver import.

A complete Envelope object additionally includes target, views, budget, query, offset, observation_ids, state, lower, upper, hypothesis counts and one evidence record per deletion combination. Every excluded branch carries a contradiction artifact. Every remaining branch carries upper and negative-lower support artifacts or an explicit conservative domain fallback. `check_envelope` rejects missing/duplicate branches, different boxes/observation rows, depth-dependent rows, incompatible queries and invalid arithmetic. It verifies a declared finite union; camera/scene authenticity is external.

## Run output

`state.json` stores the config/input/source/environment signature. `records/<hash>.json` is the atomic unit for resume. Each record has track, method, original_depths, depths, state, status_before/after, individually detected claims, edits, optional group conflict/envelopes, certificate checks, timing and memory fields. Group contradictions never fill individual detection fields by implication. `records.jsonl` is rebuilt from the per-record checkpoints after a complete run. Interrupted runs can resume using the same input signature.

Global blocks have separate cached point/depth/history records. The BA-style diagnostic changes poses and records its different information regime. Failed or nonconverged baselines retain original predictions in the reported depth comparison; their failure state must remain visible. A numeric estimate is not labeled verified without rebuilding and checking its claimed intervals.

`sampling.json` ties unique observation IDs to frame/pixel coordinates, manifest/cache identities, input signature and calibration hash. Real evaluation checks its input identity against the run state and rejects mismatches. It reads evaluation reference maps only after inference. A materialized-map index stores method, optical_z convention, sampling/results hashes and each output map hash.

`metrics.json` contains raw per-scene/seed/method records and scene aggregates. Scope is explicit: track-sampled, full-grid sparse-edits or synthetic. Undefined denominators give null. Do not compare scopes or metric/relative calibration regimes without reporting the difference.
