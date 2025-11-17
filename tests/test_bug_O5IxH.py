# tests/test_bug_O5IxH.py
import src.ir.types as tp
import src.ir.typescript_types as tst

def test_bug_O5IxH():
    # From bugs/O5IxH/202/Main.ts

    swishest_classifier = tp.SimpleClassifier(
        "Swishest",
        field_signatures=[tp.FieldInfo("cuter", tst.StringType())],
        method_signatures=[tp.MethodInfo("mcconnell", [], tst.BooleanType())]
    )

    k_param_tilts = tp.TypeParameter("K", bound=tst.StringType())
    s_param_tilts = tp.TypeParameter("S")
    w_param_tilts = tp.TypeParameter("W")

    tilts_constructor = tp.TypeConstructor(
        "Tilts",
        [k_param_tilts, s_param_tilts, w_param_tilts],
        supertypes=[swishest_classifier]
    )

    m_param = tp.TypeParameter("M")
    t_param = tp.TypeParameter("T", bound=m_param)
    
    hard_classifier = tp.SimpleClassifier(
        "Hard",
        structural=True,
        method_signatures=[
            tp.MethodInfo(
                "snippet",
                [tst.NumberType(), tilts_constructor.new([tst.StringType(), m_param, t_param])],
                tst.VoidType()
            )
        ]
    )
    hard_constructor = tp.TypeConstructor(
        "Hard",
        [m_param, t_param],
        classifier=hard_classifier
    )

    rungs_type = tp.SimpleClassifier(
        "Rungs",
        supertypes=[hard_constructor.new([tst.BigIntegerType(), tst.BigIntegerType()])],
        structural=True,
        method_signatures=[
            tp.MethodInfo("recessing", [tst.NumberType()], tst.NumberType())
        ]
    )

    hard_string_string = hard_constructor.new([tst.StringType(), tst.StringType()])

    # This should be false
    assert not rungs_type.is_subtype(hard_string_string)
