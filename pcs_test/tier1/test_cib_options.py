from textwrap import dedent
from unittest import TestCase

from lxml import etree

from pcs_test.tools.assertions import AssertPcsMixin
from pcs_test.tools.cib import get_assert_pcs_effect_mixin
from pcs_test.tools.misc import get_test_resource as rc
from pcs_test.tools.misc import (
    get_tmp_file,
    skip_unless_crm_rule,
    skip_unless_pacemaker_supports_rsc_and_op_rules,
    write_data_to_tmpfile,
    write_file_to_tmpfile,
)
from pcs_test.tools.pcs_runner import PcsRunner
from pcs_test.tools.xml import XmlManipulation

empty_cib = rc("cib-empty.xml")
empty_cib_rules = rc("cib-empty-3.4.xml")


class TestDefaultsMixin:
    def setUp(self):
        # pylint: disable=invalid-name
        self.temp_cib = get_tmp_file("tier1_cib_options")
        self.pcs_runner = PcsRunner(self.temp_cib.name)

    def tearDown(self):
        # pylint: disable=invalid-name
        self.temp_cib.close()


class DefaultsConfigMixin(TestDefaultsMixin, AssertPcsMixin):
    cli_command = []
    prefix = ""

    def test_success(self):
        xml_rsc = """
            <rsc_defaults>
                <meta_attributes id="rsc-set1" score="10">
                    <nvpair id="rsc-set1-nv1" name="name1" value="rsc1"/>
                    <nvpair id="rsc-set1-nv2" name="name2" value="rsc2"/>
                </meta_attributes>
                <meta_attributes id="rsc-setA">
                    <nvpair id="rsc-setA-nv1" name="name1" value="rscA"/>
                    <nvpair id="rsc-setA-nv2" name="name2" value="rscB"/>
                </meta_attributes>
            </rsc_defaults>
        """
        xml_op = """
            <op_defaults>
                <meta_attributes id="op-set1" score="10">
                    <nvpair id="op-set1-nv1" name="name1" value="op1"/>
                    <nvpair id="op-set1-nv2" name="name2" value="op2"/>
                </meta_attributes>
                <meta_attributes id="op-setA">
                    <nvpair id="op-setA-nv1" name="name1" value="opA"/>
                    <nvpair id="op-setA-nv2" name="name2" value="opB"/>
                </meta_attributes>
            </op_defaults>
        """
        xml_manip = XmlManipulation.from_file(empty_cib)
        xml_manip.append_to_first_tag_name("configuration", xml_rsc, xml_op)
        write_data_to_tmpfile(str(xml_manip), self.temp_cib)

        self.assert_pcs_success(
            self.cli_command,
            stdout_full=dedent(
                f"""\
                Meta Attrs: {self.prefix}-set1 score=10
                  name1={self.prefix}1
                  name2={self.prefix}2
                Meta Attrs: {self.prefix}-setA
                  name1={self.prefix}A
                  name2={self.prefix}B
            """
            ),
        )

    def test_success_rule(self):
        xml_template = """<{tag}_defaults>
            <meta_attributes id="{tag}-set1">
                <rule id="{tag}-set1-rule" boolean-op="and" score="INFINITY">
                    <rule id="{tag}-set1-rule-rule" boolean-op="or" score="0">
                        <expression id="{tag}-set1-rule-rule-expr"
                            operation="defined" attribute="attr1"
                        />
                        <expression id="{tag}-set1-rule-rule-expr-1"
                            attribute="attr2" operation="gte"
                            type="number" value="12"
                        />
                        <expression id="{tag}-set1-rule-rule-expr-2"
                            attribute="attr3" operation="lt"
                            type="version" value="3.2.1"
                        />
                        <expression id="{tag}-set1-rule-rule-expr-3"
                            attribute="attr4" operation="ne"
                            type="string" value="test"
                        />
                        <expression id="{tag}-set1-rule-rule-expr-4"
                            attribute="attr5" operation="lt" value="3"
                        />
                    </rule>
                    <rule id="{tag}-set1-rule-rule-1" boolean-op="or" score="0">
                        <date_expression id="{tag}-set1-rule-rule-1-expr"
                            operation="gt" start="2018-05-17T13:28:19"
                        />
                        <date_expression id="{tag}-set1-rule-rule-1-expr-1"
                            operation="in_range"
                            start="2019-01-01" end="2019-03-15"
                        />
                        <date_expression id="{tag}-set1-rule-rule-1-expr-2"
                             operation="in_range" start="2019-05-01"
                        >
                            <duration id="{tag}-set1-rule-rule-1-expr-2-duration"
                                months="2"
                            />
                        </date_expression>
                        <date_expression id="{tag}-set1-rule-rule-1-expr-3"
                            operation="date_spec"
                        >
                            <date_spec id="{tag}-set1-rule-rule-1-expr-3-datespec"
                                months="7-8" weekdays="6-7" years="2019"
                            />
                        </date_expression>
                        <date_expression id="{tag}-set1-rule-rule-1-expr-4"
                            operation="in_range" end="2019-12-15"
                        />
                    </rule>
                </rule>
                <nvpair id="{tag}-set1-nam1" name="nam1" value="val1"/>
                <nvpair id="{tag}-set1-nam2" name="nam2" value="val2"/>
            </meta_attributes>
        </{tag}_defaults>"""
        xml_rsc = xml_template.format(tag="rsc")
        xml_op = xml_template.format(tag="op")
        xml_manip = XmlManipulation.from_file(empty_cib)
        xml_manip.append_to_first_tag_name("configuration", xml_rsc, xml_op)
        write_data_to_tmpfile(str(xml_manip), self.temp_cib)

        self.assert_pcs_success(
            self.cli_command,
            stdout_full=dedent(
                f"""\
                Meta Attrs: {self.prefix}-set1
                  nam1=val1
                  nam2=val2
                  Rule: boolean-op=and score=INFINITY
                    Rule: boolean-op=or score=0
                      Expression: defined attr1
                      Expression: attr2 gte number 12
                      Expression: attr3 lt version 3.2.1
                      Expression: attr4 ne string test
                      Expression: attr5 lt 3
                    Rule: boolean-op=or score=0
                      Expression: date gt 2018-05-17T13:28:19
                      Expression: date in_range 2019-01-01 to 2019-03-15
                      Expression: date in_range 2019-05-01 to duration
                        Duration: months=2
                      Expression:
                        Date Spec: months=7-8 weekdays=6-7 years=2019
                      Expression: date in_range to 2019-12-15
            """
            ),
        )

    xml_expired_template = """<{tag}_defaults>
        <meta_attributes id="{tag}-set1">
            <rule id="{tag}-set1-rule" boolean-op="and" score="INFINITY">
                <date_expression id="{tag}-set1-rule-expr"
                    operation="gt" start="3000-01-01"
                />
            </rule>
            <nvpair id="{tag}-set1-name" name="name1" value="value1"/>
        </meta_attributes>
        <meta_attributes id="{tag}-set2">
            <rule id="{tag}-set2-rule" boolean-op="and" score="INFINITY">
                <date_expression id="{tag}-set2-rule-expr"
                    operation="lt" end="1000-01-01"
                />
            </rule>
            <nvpair id="{tag}-set2-name" name="name2" value="value2"/>
        </meta_attributes>
        <meta_attributes id="{tag}-set3">
            <rule id="{tag}-set3-rule" boolean-op="and" score="INFINITY">
                <date_expression id="{tag}-set3-rule-expr"
                    operation="in_range" start="1000-01-01" end="3000-01-01"
                />
            </rule>
            <nvpair id="{tag}-set3-name" name="name3" value="value3"/>
        </meta_attributes>
    </{tag}_defaults>"""

    @skip_unless_crm_rule()
    def test_success_rule_expired(self):
        xml_rsc = self.xml_expired_template.format(tag="rsc")
        xml_op = self.xml_expired_template.format(tag="op")
        xml_manip = XmlManipulation.from_file(empty_cib)
        xml_manip.append_to_first_tag_name("configuration", xml_rsc, xml_op)
        write_data_to_tmpfile(str(xml_manip), self.temp_cib)

        self.assert_pcs_success(
            self.cli_command,
            stdout_full=dedent(
                f"""\
                Meta Attrs (not yet in effect): {self.prefix}-set1
                  name1=value1
                  Rule (not yet in effect): boolean-op=and score=INFINITY
                    Expression: date gt 3000-01-01
                Meta Attrs: {self.prefix}-set3
                  name3=value3
                  Rule: boolean-op=and score=INFINITY
                    Expression: date in_range 1000-01-01 to 3000-01-01
            """
            ),
        )

    @skip_unless_crm_rule()
    def test_success_rule_expired_all(self):
        xml_rsc = self.xml_expired_template.format(tag="rsc")
        xml_op = self.xml_expired_template.format(tag="op")
        xml_manip = XmlManipulation.from_file(empty_cib)
        xml_manip.append_to_first_tag_name("configuration", xml_rsc, xml_op)
        write_data_to_tmpfile(str(xml_manip), self.temp_cib)

        self.assert_pcs_success(
            self.cli_command + ["--all"],
            stdout_full=dedent(
                f"""\
                Meta Attrs (not yet in effect): {self.prefix}-set1
                  name1=value1
                  Rule (not yet in effect): boolean-op=and score=INFINITY
                    Expression: date gt 3000-01-01
                Meta Attrs (expired): {self.prefix}-set2
                  name2=value2
                  Rule (expired): boolean-op=and score=INFINITY
                    Expression: date lt 1000-01-01
                Meta Attrs: {self.prefix}-set3
                  name3=value3
                  Rule: boolean-op=and score=INFINITY
                    Expression: date in_range 1000-01-01 to 3000-01-01
            """
            ),
        )


class RscDefaultsConfig(
    DefaultsConfigMixin,
    TestCase,
):
    cli_command = ["resource", "defaults"]
    prefix = "rsc"

    @skip_unless_pacemaker_supports_rsc_and_op_rules()
    def test_success_rules_rsc_op(self):
        xml = """
            <rsc_defaults>
                <meta_attributes id="X">
                    <rule id="X-rule" boolean-op="and" score="INFINITY">
                        <rsc_expression id="X-rule-rsc-Dummy" type="Dummy"/>
                    </rule>
                    <nvpair id="X-nam1" name="nam1" value="val1"/>
                </meta_attributes>
            </rsc_defaults>
        """
        xml_manip = XmlManipulation.from_file(empty_cib_rules)
        xml_manip.append_to_first_tag_name("configuration", xml)
        write_data_to_tmpfile(str(xml_manip), self.temp_cib)

        self.assert_pcs_success(
            self.cli_command,
            stdout_full=dedent(
                """\
                Meta Attrs: X
                  nam1=val1
                  Rule: boolean-op=and score=INFINITY
                    Expression: resource ::Dummy
            """
            ),
        )


class OpDefaultsConfig(
    DefaultsConfigMixin,
    TestCase,
):
    cli_command = ["resource", "op", "defaults"]
    prefix = "op"

    @skip_unless_pacemaker_supports_rsc_and_op_rules()
    def test_success_rules_rsc_op(self):
        xml = """
            <op_defaults>
                <meta_attributes id="X">
                    <rule id="X-rule" boolean-op="and" score="INFINITY">
                        <rsc_expression id="X-rule-rsc-Dummy" type="Dummy"/>
                        <op_expression id="X-rule-op-monitor" name="monitor"/>
                    </rule>
                    <nvpair id="X-nam1" name="nam1" value="val1"/>
                </meta_attributes>
            </op_defaults>
        """
        xml_manip = XmlManipulation.from_file(empty_cib_rules)
        xml_manip.append_to_first_tag_name("configuration", xml)
        write_data_to_tmpfile(str(xml_manip), self.temp_cib)

        self.assert_pcs_success(
            self.cli_command,
            stdout_full=dedent(
                """\
                Meta Attrs: X
                  nam1=val1
                  Rule: boolean-op=and score=INFINITY
                    Expression: resource ::Dummy
                    Expression: op monitor
            """
            ),
        )


class DefaultsSetCreateMixin(TestDefaultsMixin, AssertPcsMixin):
    cli_command = []
    cib_tag = ""

    def setUp(self):
        super().setUp()
        write_file_to_tmpfile(empty_cib, self.temp_cib)

    def test_no_args(self):
        self.assert_effect(
            self.cli_command + ["set", "create"],
            dedent(
                f"""\
                <{self.cib_tag}>
                    <meta_attributes id="{self.cib_tag}-meta_attributes"/>
                </{self.cib_tag}>
            """
            ),
            output=(
                "Warning: Defaults do not apply to resources which override "
                "them with their own defined values\n"
            ),
        )

    def test_success(self):
        self.assert_effect(
            self.cli_command
            + "set create id=mine score=10 meta nam1=val1 nam2=val2 --force".split(),
            dedent(
                f"""\
                <{self.cib_tag}>
                    <meta_attributes id="mine" score="10">
                        <nvpair id="mine-nam1" name="nam1" value="val1"/>
                        <nvpair id="mine-nam2" name="nam2" value="val2"/>
                    </meta_attributes>
                </{self.cib_tag}>
            """
            ),
            output=(
                "Warning: Defaults do not apply to resources which override "
                "them with their own defined values\n"
            ),
        )

    def test_success_rule(self):
        self.assert_effect(
            self.cli_command
            + (
                "-- set create id=mine score=10 meta nam1=val1 nam2=val2 "
                "rule (date gt 2018-05-17T13:28:19 or "
                "date in_range 2019-01-01 to 2019-03-15 or "
                "date in_range 2019-05-01 to duration months=2 or "
                "date-spec years=2019 months=7-8 weekdays=6-7 or "
                "date in_range to 2019-12-15)"
            ).split(),
            dedent(
                f"""\
                <{self.cib_tag}>
                    <meta_attributes id="mine" score="10">
                        <rule id="mine-rule" boolean-op="or" score="INFINITY">
                            <date_expression id="mine-rule-expr"
                                operation="gt" start="2018-05-17T13:28:19"
                            />
                            <date_expression id="mine-rule-expr-1"
                                operation="in_range"
                                start="2019-01-01" end="2019-03-15"
                            />
                            <date_expression id="mine-rule-expr-2"
                                operation="in_range" start="2019-05-01"
                            >
                                <duration id="mine-rule-expr-2-duration"
                                    months="2"
                                />
                            </date_expression>
                            <date_expression id="mine-rule-expr-3"
                                operation="date_spec"
                            >
                                <date_spec
                                    id="mine-rule-expr-3-datespec"
                                    months="7-8" weekdays="6-7" years="2019"
                                />
                            </date_expression>
                            <date_expression id="mine-rule-expr-4"
                                  operation="in_range" end="2019-12-15"
                            />
                        </rule>
                        <nvpair id="mine-nam1" name="nam1" value="val1"/>
                        <nvpair id="mine-nam2" name="nam2" value="val2"/>
                    </meta_attributes>
                </{self.cib_tag}>
            """
            ),
            output=(
                "Warning: Defaults do not apply to resources which override "
                "them with their own defined values\n"
            ),
        )

    def test_rule_error_messages(self):
        self.assert_pcs_fail(
            self.cli_command
            + (
                "set create id=mine score=10 meta nam1=val1 nam2=val2 "
                "rule (date gt 2018-05-1X or "
                "date in_range 2019-03-05 to 2019-01-11 or "
                "date in_range 2019-05-0X to duration months=2 months=3a x=y or "
                "date-spec years=2019 months=7-X weekdays=7-6 years=202a x=y)"
            ).split(),
            (
                "Error: '2018-05-1X' is not a valid date value, use ISO 8601 date\n"
                "Error: Since '2019-03-05' is not sooner than until '2019-01-11'\n"
                "Error: '2019-05-0X' is not a valid date value, use ISO 8601 date\n"
                "Error: '3a' is not a valid months value, use a positive integer\n"
                "Error: invalid duration option 'x', allowed options are: "
                "'hours', 'monthdays', 'months', 'moon', 'weekdays', "
                "'weeks', 'weekyears', 'years', 'yearsdays'\n"
                "Error: Duplicate options in a single (sub)expression: 'months'\n"
                "Error: '7-X' is not a valid months value, use 1..12 or 1..11-2..12\n"
                "Error: '7-6' is not a valid weekdays value, use 1..7 or 1..6-2..7\n"
                "Error: '202a' is not a valid years value, use an integer or "
                "integer-integer\n"
                "Error: invalid datespec option 'x', allowed options are: "
                "'hours', 'monthdays', 'months', 'moon', 'weekdays', "
                "'weeks', 'weekyears', 'years', 'yearsdays'\n"
                "Error: Duplicate options in a single (sub)expression: 'years'\n"
                "Error: Errors have occurred, therefore pcs is unable to continue\n"
            ),
        )


class RscDefaultsSetCreate(
    get_assert_pcs_effect_mixin(
        lambda cib: etree.tostring(
            # pylint:disable=undefined-variable
            etree.parse(cib).findall(".//rsc_defaults")[0]
        )
    ),
    DefaultsSetCreateMixin,
    TestCase,
):
    cli_command = ["resource", "defaults"]
    cib_tag = "rsc_defaults"

    @skip_unless_pacemaker_supports_rsc_and_op_rules()
    def test_success_rules_rsc_op(self):
        self.assert_effect(
            self.cli_command
            + "set create id=X meta nam1=val1 rule resource ::Dummy".split(),
            f"""\
            <{self.cib_tag}>
                <meta_attributes id="X">
                    <rule id="X-rule" boolean-op="and" score="INFINITY">
                        <rsc_expression id="X-rule-rsc-Dummy" type="Dummy"/>
                    </rule>
                    <nvpair id="X-nam1" name="nam1" value="val1"/>
                </meta_attributes>
            </{self.cib_tag}>
            """,
            output=(
                "CIB has been upgraded to the latest schema version.\n"
                "Warning: Defaults do not apply to resources which override "
                "them with their own defined values\n"
            ),
        )

    def test_node_attr_expressions(self):
        self.assert_pcs_fail(
            self.cli_command + ("set create rule defined attr").split(),
            (
                "Error: Keywords 'defined', 'not_defined', 'eq', 'ne', 'gte', "
                "'gt', 'lte' and 'lt' cannot be used in a rule in this command\n"
                "Error: Errors have occurred, therefore pcs is unable to continue\n"
            ),
        )


class OpDefaultsSetCreate(
    get_assert_pcs_effect_mixin(
        lambda cib: etree.tostring(
            # pylint:disable=undefined-variable
            etree.parse(cib).findall(".//op_defaults")[0]
        )
    ),
    DefaultsSetCreateMixin,
    TestCase,
):
    cli_command = ["resource", "op", "defaults"]
    cib_tag = "op_defaults"

    def test_rule_error_messages(self):
        self.assert_pcs_fail(
            self.cli_command
            + (
                "set create rule defined attr1 or attr2 gte number 12a or "
                "attr3 lt version 3.2.1a or attr4 ne string test or attr5 lt 3 "
            ).split(),
            (
                "Error: '12a' is not a valid number attribute value, use a "
                "floating-point number\n"
                "Error: '3.2.1a' is not a valid version attribute value, use "
                "a version number (e.g. 1, 1.2, 1.23.45, ...)\n"
                "Error: Errors have occurred, therefore pcs is unable to continue\n"
            ),
        )

    @skip_unless_pacemaker_supports_rsc_and_op_rules()
    def test_success_rules_rsc_op(self):
        self.assert_effect(
            self.cli_command
            + (
                "-- set create id=X meta nam1=val1 "
                "rule resource ::Dummy and (op start or op stop) and "
                "(defined attr1 or attr2 gte number -1.2 or "
                "attr3 lt version 3.2.1 or attr4 ne string test or attr5 lt 3) "
            ).split(),
            f"""\
            <{self.cib_tag}>
                <meta_attributes id="X">
                    <rule id="X-rule" boolean-op="and" score="INFINITY">
                        <rsc_expression id="X-rule-rsc-Dummy" type="Dummy"/>
                        <rule id="X-rule-rule" boolean-op="or" score="0">
                            <op_expression id="X-rule-rule-op-start"
                                name="start"
                            />
                            <op_expression id="X-rule-rule-op-stop"
                                name="stop"
                            />
                        </rule>
                        <rule id="X-rule-rule-1" boolean-op="or" score="0">
                            <expression id="X-rule-rule-1-expr"
                                operation="defined" attribute="attr1"
                            />
                            <expression id="X-rule-rule-1-expr-1"
                                attribute="attr2" operation="gte"
                                type="number" value="-1.2"
                            />
                            <expression id="X-rule-rule-1-expr-2"
                                attribute="attr3" operation="lt"
                                type="version" value="3.2.1"
                            />
                            <expression id="X-rule-rule-1-expr-3"
                                attribute="attr4" operation="ne"
                                type="string" value="test"
                            />
                            <expression id="X-rule-rule-1-expr-4"
                                attribute="attr5" operation="lt" value="3"
                            />
                        </rule>
                    </rule>
                    <nvpair id="X-nam1" name="nam1" value="val1"/>
                </meta_attributes>
            </{self.cib_tag}>
            """,
            output=(
                "CIB has been upgraded to the latest schema version.\n"
                "Warning: Defaults do not apply to resources which override "
                "them with their own defined values\n"
            ),
        )


class DefaultsSetDeleteMixin(TestDefaultsMixin, AssertPcsMixin):
    cli_command = []
    prefix = ""
    cib_tag = ""

    def setUp(self):
        super().setUp()
        xml_rsc = """
            <rsc_defaults>
                <meta_attributes id="rsc-set1" />
                <meta_attributes id="rsc-set2" />
                <meta_attributes id="rsc-set3" />
                <meta_attributes id="rsc-set4" />
            </rsc_defaults>
        """
        xml_op = """
            <op_defaults>
                <meta_attributes id="op-set1" />
                <meta_attributes id="op-set2" />
                <meta_attributes id="op-set3" />
                <meta_attributes id="op-set4" />
            </op_defaults>
        """
        xml_manip = XmlManipulation.from_file(empty_cib)
        xml_manip.append_to_first_tag_name("configuration", xml_rsc, xml_op)
        write_data_to_tmpfile(str(xml_manip), self.temp_cib)

    def test_success(self):
        self.assert_effect(
            [
                self.cli_command
                + f"set delete {self.prefix}-set1 {self.prefix}-set3".split(),
                self.cli_command
                + f"set remove {self.prefix}-set1 {self.prefix}-set3".split(),
            ],
            dedent(
                f"""\
                <{self.cib_tag}>
                    <meta_attributes id="{self.prefix}-set2" />
                    <meta_attributes id="{self.prefix}-set4" />
                </{self.cib_tag}>
            """
            ),
        )


class RscDefaultsSetDelete(
    get_assert_pcs_effect_mixin(
        lambda cib: etree.tostring(
            # pylint:disable=undefined-variable
            etree.parse(cib).findall(".//rsc_defaults")[0]
        )
    ),
    DefaultsSetDeleteMixin,
    TestCase,
):
    cli_command = ["resource", "defaults"]
    prefix = "rsc"
    cib_tag = "rsc_defaults"


class OpDefaultsSetDelete(
    get_assert_pcs_effect_mixin(
        lambda cib: etree.tostring(
            # pylint:disable=undefined-variable
            etree.parse(cib).findall(".//op_defaults")[0]
        )
    ),
    DefaultsSetDeleteMixin,
    TestCase,
):
    cli_command = ["resource", "op", "defaults"]
    prefix = "op"
    cib_tag = "op_defaults"


class DefaultsSetUpdateMixin(TestDefaultsMixin, AssertPcsMixin):
    cli_command = []
    prefix = ""
    cib_tag = ""

    def test_success(self):
        xml = f"""
            <{self.cib_tag}>
                <meta_attributes id="my-set">
                    <nvpair id="my-set-name1" name="name1" value="value1" />
                    <nvpair id="my-set-name2" name="name2" value="value2" />
                    <nvpair id="my-set-name3" name="name3" value="value3" />
                </meta_attributes>
            </{self.cib_tag}>
        """
        xml_manip = XmlManipulation.from_file(empty_cib)
        xml_manip.append_to_first_tag_name("configuration", xml)
        write_data_to_tmpfile(str(xml_manip), self.temp_cib)
        warnings = (
            "Warning: Defaults do not apply to resources which override "
            "them with their own defined values\n"
        )

        self.assert_effect(
            self.cli_command
            + "set update my-set meta name2=value2A name3=".split(),
            dedent(
                f"""\
                <{self.cib_tag}>
                    <meta_attributes id="my-set">
                        <nvpair id="my-set-name1" name="name1" value="value1" />
                        <nvpair id="my-set-name2" name="name2" value="value2A" />
                    </meta_attributes>
                </{self.cib_tag}>
            """
            ),
            output=warnings,
        )

        self.assert_effect(
            self.cli_command + "set update my-set meta name1= name2=".split(),
            dedent(
                f"""\
                <{self.cib_tag}>
                    <meta_attributes id="my-set" />
                </{self.cib_tag}>
            """
            ),
            output=warnings,
        )


class RscDefaultsSetUpdate(
    get_assert_pcs_effect_mixin(
        lambda cib: etree.tostring(
            # pylint:disable=undefined-variable
            etree.parse(cib).findall(".//rsc_defaults")[0]
        )
    ),
    DefaultsSetUpdateMixin,
    TestCase,
):
    cli_command = ["resource", "defaults"]
    prefix = "rsc"
    cib_tag = "rsc_defaults"


class OpDefaultsSetUpdate(
    get_assert_pcs_effect_mixin(
        lambda cib: etree.tostring(
            # pylint:disable=undefined-variable
            etree.parse(cib).findall(".//op_defaults")[0]
        )
    ),
    DefaultsSetUpdateMixin,
    TestCase,
):
    cli_command = ["resource", "op", "defaults"]
    prefix = "op"
    cib_tag = "op_defaults"


class DefaultsSetUsageMixin(TestDefaultsMixin, AssertPcsMixin):
    cli_command = []

    def test_no_args(self):
        self.assert_pcs_fail(
            self.cli_command + ["set"],
            stdout_start=f"\nUsage: pcs {' '.join(self.cli_command)} set...\n",
        )

    def test_bad_command(self):
        self.assert_pcs_fail(
            self.cli_command + ["set", "bad-command"],
            stdout_start=f"\nUsage: pcs {' '.join(self.cli_command)} set ...\n",
        )


class RscDefaultsSetUsage(
    DefaultsSetUsageMixin,
    TestCase,
):
    cli_command = ["resource", "defaults"]


class OpDefaultsSetUsage(
    DefaultsSetUsageMixin,
    TestCase,
):
    cli_command = ["resource", "op", "defaults"]


class DefaultsUpdateMixin(TestDefaultsMixin, AssertPcsMixin):
    cli_command = []
    prefix = ""
    cib_tag = ""

    def assert_success_legacy(self, update_keyword):
        write_file_to_tmpfile(empty_cib, self.temp_cib)
        warning_lines = []
        if not update_keyword:
            warning_lines.append(
                f"Deprecation Warning: This command is deprecated and will be "
                f"removed. Please use 'pcs {' '.join(self.cli_command)} "
                f"update' instead.\n"
            )
        warning_lines.append(
            "Warning: Defaults do not apply to resources which override "
            "them with their own defined values\n"
        )
        warnings = "".join(warning_lines)

        command = self.cli_command[:]
        if update_keyword:
            command.append("update")

        self.assert_effect(
            command + "name1=value1 name2=value2 name3=value3".split(),
            dedent(
                f"""\
                <{self.cib_tag}>
                    <meta_attributes id="{self.cib_tag}-meta_attributes">
                        <nvpair id="{self.cib_tag}-meta_attributes-name1"
                            name="name1" value="value1"
                        />
                        <nvpair id="{self.cib_tag}-meta_attributes-name2"
                            name="name2" value="value2"
                        />
                        <nvpair id="{self.cib_tag}-meta_attributes-name3"
                            name="name3" value="value3"
                        />
                    </meta_attributes>
                </{self.cib_tag}>
            """
            ),
            output=warnings,
        )

        self.assert_effect(
            command + "name2=value2A name3=".split(),
            dedent(
                f"""\
                <{self.cib_tag}>
                    <meta_attributes id="{self.cib_tag}-meta_attributes">
                        <nvpair id="{self.cib_tag}-meta_attributes-name1"
                            name="name1" value="value1"
                        />
                        <nvpair id="{self.cib_tag}-meta_attributes-name2"
                            name="name2" value="value2A"
                        />
                    </meta_attributes>
                </{self.cib_tag}>
            """
            ),
            output=warnings,
        )

        self.assert_effect(
            command + "name1= name2=".split(),
            dedent(
                f"""\
                <{self.cib_tag}>
                    <meta_attributes id="{self.cib_tag}-meta_attributes" />
                </{self.cib_tag}>
            """
            ),
            output=warnings,
        )

    def test_deprecated(self):
        self.assert_success_legacy(False)

    def test_legacy(self):
        self.assert_success_legacy(True)


class RscDefaultsUpdate(
    get_assert_pcs_effect_mixin(
        lambda cib: etree.tostring(
            # pylint:disable=undefined-variable
            etree.parse(cib).findall(".//rsc_defaults")[0]
        )
    ),
    DefaultsUpdateMixin,
    TestCase,
):
    cli_command = ["resource", "defaults"]
    prefix = "rsc"
    cib_tag = "rsc_defaults"


class OpDefaultsUpdate(
    get_assert_pcs_effect_mixin(
        lambda cib: etree.tostring(
            # pylint:disable=undefined-variable
            etree.parse(cib).findall(".//op_defaults")[0]
        )
    ),
    DefaultsUpdateMixin,
    TestCase,
):
    cli_command = ["resource", "op", "defaults"]
    prefix = "op"
    cib_tag = "op_defaults"
