def fixture_resources_for_ids():
    return """
        <resources>
            <primitive class="ocf" id="id1" provider="pacemaker" type="Dummy"/>
            <primitive class="ocf" id="id2" provider="pacemaker" type="Dummy"/>
        </resources>
    """


def fixture_tags_xml(tag_with_ids):
    return (
        "<tags>"
        + "".join(
            '<tag id="{tag_id}">'.format(tag_id=tag_id)
            + "".join('<obj_ref id="{id}"/>'.format(id=id) for id in id_list)
            + "</tag>"
            for tag_id, id_list in tag_with_ids
        )
        + "</tags>"
    )


def fixture_constraints_for_tags(tag_list):
    return (
        "<constraints>"
        + "".join(
            f"<rsc_location id='location-{tag}' rsc='{tag}' node='nodeN' "
            "score='100'/>"
            for tag in tag_list
        )
        + "</constraints>"
    )
