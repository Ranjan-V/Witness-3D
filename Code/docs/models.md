# Frozen model dependencies and API review

No source repository or checkpoint was downloaded, imported or executed during authoring. Only read-only official online documentation/source was inspected on 2026-11-02. Upstream revisions are not pinned to an unverified commit. Future runs hash local Python sources and record package versions; the user must select and record working revisions.

## DA-V2 metric Small

Primary source: [official metric-depth README](https://github.com/DepthAnything/Depth-Anything-V2/tree/main/metric_depth) and [metric dpt source](https://raw.githubusercontent.com/DepthAnything/Depth-Anything-V2/main/metric_depth/depth_anything_v2/dpt.py). Use the local `metric_depth` subdirectory as `repository`. The relative-depth root exposes a similarly named class and is not interchangeable.

The adapter constructs `DepthAnythingV2` with vits, feature width 64, output channels [48,96,192,384] and max_depth=20 for the indoor Hypersim metric Small checkpoint. The outdoor VKITTI variant requires its corresponding checkpoint and max_depth=80. Local weights are loaded strictly. Official documentation identifies the metric Small model as 24.8M parameters. The default relative model is not accepted as metric depth.

Inputs are uint8 RGB. Upstream resizing is reused, with aspect preservation and multiples of 14; normalization uses the documented ImageNet statistics. The adapter forwards a microbatch directly rather than using `image2tensor`, because that helper chooses a device implicitly. Output is resized to the original image grid using the metric implementation's bilinear/align_corners convention. External camera intrinsics therefore describe that original grid. Boundary uncertainty and resampling effects still need empirical calibration.

## MiDaS v2.1 Small

Sources: [official repository](https://github.com/isl-org/MiDaS), [hub API](https://raw.githubusercontent.com/isl-org/MiDaS/master/hubconf.py), [small network source](https://raw.githubusercontent.com/isl-org/MiDaS/master/midas/midas_net_custom.py) and [backbone factory](https://raw.githubusercontent.com/isl-org/MiDaS/master/midas/blocks.py). This compact control returns relative inverse depth, not meters.

Provide local MiDaS source, local `midas_v21_small_256.pt` weights, and a local gen-efficientnet-pytorch source checkout with its hub entrypoint. Upstream construction would otherwise request an online EfficientNet source/backbone even for a local depth checkpoint. The adapter temporarily replaces only that construction factory with a local `torch.hub.load(..., source='local', pretrained=False)` call, restores it afterward, and loads the complete local MiDaS checkpoint. Model construction should occur once in a single thread/process. MiDaS' own checkpoint loader may use historical PyTorch loading conventions; only use a trusted official checkpoint. This adapter requires environment verification with compatible timm/torchvision/upstream revisions.

Official small preprocessing is loaded from local hub source; no pretrained hub model call is made. Predictions are returned on the original image grid with the documented bicubic interpolation convention. Before geometry, fit `1/z = scale * inverse + shift`, scale>0, on image-only triangulated anchors from a separate calibration manifest. The calibration command rejects weak parallax and large reprojection residuals. It records calibration frame IDs and evaluation extraction refuses any overlap. At least eight valid samples and inverse-depth variation are required. Failed or nonpositive calibration values cause exclusion/abstention, not reference-depth alignment.

Calibration is heuristic and provides no certified uncertainty on scale/shift. Strict metric guarantees for this control are conditional on that adapter conversion being conservative; the primary claim should be tested with the actual metric checkpoint first.

## Future adapter verification checklist

Record checkpoint hash, upstream source hash, model license, task/depth convention, preprocessing grid, max_depth and package versions. Compare one future local adapter output against the corresponding official inference function under identical preprocessing before running a benchmark. This authoring task did not perform that comparison. Confirm that no dependency tries to retrieve missing assets with Kaggle networking disabled.
