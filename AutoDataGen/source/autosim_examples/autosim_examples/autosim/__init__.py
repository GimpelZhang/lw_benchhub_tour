from autosim import register_pipeline

register_pipeline(
    id="AutoSimPipeline-FrankaCubeLift-v0",
    entry_point=f"{__name__}.pipelines.franka_lift_cube:FrankaCubeLiftPipeline",
    cfg_entry_point=f"{__name__}.pipelines.franka_lift_cube:FrankaCubeLiftPipelineCfg",
)

register_pipeline(
    id="AutoSimPipeline-DoublePiperKitchenPnp-v0",
    entry_point=f"{__name__}.pipelines.doublepiper_kitchen_pnp:DoublePiperKitchenPnpPipeline",
    cfg_entry_point=f"{__name__}.pipelines.doublepiper_kitchen_pnp:DoublePiperKitchenPnpPipelineCfg",
)
