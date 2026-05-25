from pathlib import Path


def load_app_namespace():
    source = Path("app.py").read_text(encoding="utf-8-sig")
    namespace = {"__name__": "app", "__file__": str(Path("app.py").resolve())}
    exec(compile(source, "app.py", "exec"), namespace)
    return namespace


def test_parsed_drawing_uses_acr_token_between_underscores():
    ns = load_app_namespace()

    product, drawing, spec, alloy, item_cat, length = ns["split_material_description"](
        "FPDT_ACR2267_7X0.47X0.25-JUMBO#_300370_C"
    )

    assert product == "PDT"
    assert drawing == "ACR2267"
    assert spec == "ACR2267_7X0.47X0.25"
    assert alloy == "300370_C"
    assert item_cat == "PDT"
    assert length == "coil"


def test_parsed_drawing_uses_igb_token_between_underscores():
    ns = load_app_namespace()

    product, drawing, spec, alloy, item_cat, length = ns["split_material_description"](
        "FMPE_IGB0800_MPC_1000.0MM_6101B_T63"
    )

    assert product == "MPE"
    assert drawing == "IGB0800"
    assert item_cat == "IP-BAR"
