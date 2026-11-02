# Data contracts and preparation

No dataset was downloaded or opened. Adapters consume local, user-prepared data. Calibration, staticness, registration, visibility and timing quality are premises, not facts proved by the verifier. A canonical JSON manifest describes undistorted pinhole RGB images, known c2w poses, image dimensions and optional separately accessed registered optical-z reference depths. All poses use right/down/forward camera axes and meters.

## TUM RGB-D

[Official format source](https://cvg.cit.tum.de/data/datasets/rgbd-dataset/file_formats). Timestamp lists contain image paths. Trajectories use timestamp, tx ty tz qx qy qz qw, camera-to-world. Depth PNG values use 5000 units/m and zero invalid; this is not the millimeter scale of the other RGB-D datasets. The official registration/calibration documentation was examined.

The adapter performs one-to-one timestamp matching with explicit maximum differences, no interpolation. Timing/pose error remains. Provide K for the actual exported rectified RGB grid, and registered depth on that same grid. TUM camera variants differ; no universal K is guessed. If rectifying RGB, transform reference depth consistently with a z-buffer and preserve optical-axis units. Depth values are evaluation-only and must never guide feature selection, interval widths, box bounds or repair.

## 7-Scenes

[Official release](https://www.microsoft.com/en-us/research/project/rgb-d-dataset-7-scenes/). Official pose files are 4x4 c2w. Depth is millimeters, invalid 65535. The release states that RGB/depth cameras are uncalibrated and only a default depth-camera K was used for tracking. That K must not be silently assigned to RGB.

The adapter requires an independently vetted RGB calibration and a registered depth export, by default `.depth.proj.png`, plus explicit provenance. It does not pretend to solve unavailable calibration. Keep official train/test sequence splits and state which export/calibration was used; public derived calibrations require their own audit. Estimated KinectFusion poses are not perfect physical poses.

## Sampled ScanNet (original dataset, not ScanNet++)

[Official SensorData source](https://github.com/ScanNet/ScanNet/blob/master/SensReader/python/SensorData.py) exposes separate color/depth intrinsics/extrinsics, depth shift and frame poses. Consume sampled decoded RGB, pose text and already RGB-registered reference depth. Do not assume equal RGB/depth resolution or that resizing alone registers sensors.

Specify whether exported c2w poses refer to color or depth. For a depth-frame pose, supply normalized T_color_depth satisfying x_color=T_color_depth*x_depth. Then T_world_color=T_world_depth*inverse(T_color_depth). The conversion is implemented and tested in write-only tests. Verify what your exporter means by extrinsic matrices before constructing this normalized transform. Use the actual depth_shift; the example 1000 is not an implicit parser default. Invalid nonfinite tracking poses are excluded and exclusion counts should be recorded. Official data access requires accepting dataset terms; this task bypasses nothing.

## ETH3D

[Official documentation](https://www.eth3d.net/documentation). Use high-resolution multi-view *training* subsets when local reference geometry/depth annotations are available and appropriate. Camera calibration is COLMAP format: image records carry q_w q_x q_y q_z and world-to-camera translations. The parser converts to c2w and accepts PINHOLE or SIMPLE_PINHOLE only. Distorted models, including fisheye, are rejected.

Provide pinhole undistorted images and registered optical-z `.npy` reference maps in meters, with a documented export. Raw laser-scan depth formats/coordinate mappings are not guessed, and test-server references are not assumed available. Full point-cloud MVS benchmark scoring is not equivalent to sampled depth error; use official evaluation separately if pursuing reconstruction claims. Resize large DSLR images offline with documented camera transforms before this resource-limited pipeline.

## Required local layout

```text
prepared_scene/
  calibration/K_rgb_rectified.txt
  rgb-or-color/...
  registered_depth/...
  pose/...
  manifest.json
```

Paths are configurable, and native adapter patterns are documented in `configs/manifests/`. No Kaggle path is hardcoded in Python. Manifest template provenance fields start with `REQUIRED` and must be replaced with the actual procedure; unchanged templates fail intentionally. Assertions in a manifest do not establish calibration correctness.

Inference accesses `FrameInput.image()` and camera metadata only. Reference depths are wrapped in `ReferenceDepth` and loaded only by explicit post-inference evaluation. The synthetic generator similarly returns `Inputs` and `Truth` separately.
