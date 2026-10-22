"""Parsed-model contracts for completed Instantiation BASE and EXTENDED APIs."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import component, instantiation
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Component, Design, DesignConfiguration, TypeDefinitions
from org.accellera.ipxact.v1685_2022.generator_chain import GeneratorChain

NS = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


def parse(xml: str, root_type):
    return XmlDocument.parser().from_string(xml, root_type)


def instantiations_of(root):
    container = root.model.instantiations
    return container.component_instantiation_or_design_instantiation_or_design_configuration_instantiation


def component_document(file_set_name: str = "src"):
    return parse(
        f'''<component xmlns="{NS}">
<vendor>v</vendor><library>l</library><name>c</name><version>1</version>
<busInterfaces><busInterface><name>bus</name>
<busType vendor="v" library="l" name="bus" version="1"/>
<abstractionTypes><abstractionType><abstractionRef vendor="v" library="l" name="abs" version="1"/>
</abstractionType></abstractionTypes></busInterface></busInterfaces>
<model><instantiations>
<componentInstantiation><name>ci</name><fileSetRef><localName>{file_set_name}</localName></fileSetRef></componentInstantiation>
<designInstantiation><name>di</name><designRef vendor="v" library="l" name="design" version="1"/></designInstantiation>
<designConfigurationInstantiation><name>dci</name>
<designConfigurationRef vendor="v" library="l" name="dc" version="1"/>
</designConfigurationInstantiation>
</instantiations></model></component>''',
        Component,
    )


def design_document():
    return parse(
        f'''<design xmlns="{NS}"><vendor>v</vendor><library>l</library><name>design</name><version>1</version>
<componentInstances><componentInstance><instanceName>u0</instanceName>
<componentRef vendor="v" library="l" name="component" version="1"/>
</componentInstance></componentInstances></design>''',
        Design,
    )


def design_configuration_document(name="dc", version="1"):
    return parse(
        f'''<designConfiguration xmlns="{NS}"><vendor>v</vendor><library>l</library>
<name>{name}</name><version>{version}</version><designRef vendor="v" library="l" name="design" version="1"/>
<interconnectionConfiguration><interconnectionRef>bus_link</interconnectionRef>
<abstractorInstances><abstractorInstance><instanceName>a0</instanceName>
<abstractorRef vendor="v" library="l" name="abstractor" version="1"/><viewName>rtl</viewName>
</abstractorInstance></abstractorInstances></interconnectionConfiguration></designConfiguration>''',
        DesignConfiguration,
    )


def test_nested_reference_id_getters_restore_parsed_ownership():
    component_root = component_document()
    abstraction_type = component_root.bus_interfaces.bus_interface[0].abstraction_types.abstraction_type[0]
    abstraction_ref_id = instantiation.getAbstractionTypeAbstractionRefID(get_handle(abstraction_type))
    assert resolve_handle(abstraction_ref_id).name == "abs"

    design_root = design_document()
    component_instance = design_root.component_instances.component_instance[0]
    component_ref_id = instantiation.getComponentInstanceComponentRefID(get_handle(component_instance))
    assert resolve_handle(component_ref_id).name == "component"

    dc_root = design_configuration_document()
    abstractor_instance = dc_root.interconnection_configuration[0].abstractor_instances[0].abstractor_instance[0]
    abstractor_ref_id = instantiation.getAbstractorInstanceAbstractorRefID(get_handle(abstractor_instance))
    assert resolve_handle(abstractor_ref_id).name == "abstractor"

    with pytest.raises(TgiError) as invalid:
        instantiation.getAbstractionTypeAbstractionRefID(get_handle(object()))
    assert invalid.value.fault_code == TgiFaultCode.INVALID_ID


def test_design_reference_lookups_use_exact_registered_vlnv_and_distinct_ref_handles():
    registry.clear()
    try:
        owner = component_document()
        design_inst = instantiations_of(owner)[1]
        design_inst_id = get_handle(design_inst)
        design_ref_id = instantiation.getDesignInstantiationDesignRefID(design_inst_id)
        assert resolve_handle(design_ref_id).name == "design"
        assert instantiation.getDesignInstantiationDesignRefByVLNV(design_inst_id) == ("v", "l", "design", "1")

        decoy = parse(
            f'<design xmlns="{NS}"><vendor>v</vendor><library>l</library><name>design</name>'
            f"<version>2</version></design>",
            Design,
        )
        target = design_document()
        with pytest.raises(TgiError) as missing_design:
            instantiation.getDesignInstantiationDesignRefByID(design_inst_id)
        assert missing_design.value.fault_code == TgiFaultCode.NOT_FOUND

        registry.register(decoy, ("v", "l", "design", "2"))
        registry.register(target, ("v", "l", "design", "1"))
        with pytest.raises(TgiError) as duplicate:
            registry.register(design_document(), ("v", "l", "design", "1"))
        assert duplicate.value.fault_code == TgiFaultCode.ALREADY_EXISTS
        target_id = instantiation.getDesignInstantiationDesignRefByID(design_inst_id)
        assert target_id == get_handle(target)
        assert target_id != get_handle(decoy)

        with pytest.raises(TgiError) as missing:
            instantiation.getDesignConfigurationInstantiationDesignConfigurationRefByID(
                get_handle(instantiations_of(owner)[2])
            )
        assert missing.value.fault_code == TgiFaultCode.NOT_FOUND

        wrong_type = component_document()
        registry.register(wrong_type, ("v", "l", "dc", "1"))
        dci = instantiations_of(owner)[2]
        with pytest.raises(TgiError) as wrong:
            instantiation.getDesignConfigurationInstantiationDesignConfigurationRefByID(get_handle(dci))
        assert wrong.value.fault_code == TgiFaultCode.NOT_FOUND
    finally:
        registry.clear()


def test_design_configuration_reference_id_resolves_root_separately_from_ref_node():
    registry.clear()
    try:
        owner = component_document()
        dci = instantiations_of(owner)[2]
        dci_id = get_handle(dci)
        parsed_ref_id = instantiation.getDesignConfigurationInstantiationDesignConfigurationRefID(dci_id)
        assert resolve_handle(parsed_ref_id).name == "dc"

        target = design_configuration_document()
        registry.register(target, ("v", "l", "dc", "1"))
        target_id = instantiation.getDesignConfigurationInstantiationDesignConfigurationRefByID(dci_id)
        assert target_id == get_handle(target)
        assert target_id != parsed_ref_id

        with pytest.raises(TgiError) as invalid:
            instantiation.getDesignConfigurationInstantiationDesignConfigurationRefID(get_handle(owner))
        assert invalid.value.fault_code == TgiFaultCode.INVALID_ID
    finally:
        registry.clear()


def test_remaining_parsed_base_getters_and_wrong_type_faults():
    definitions = parse(
        f'''<typeDefinitions xmlns="{NS}"><vendor>v</vendor><library>l</library><name>types</name><version>1</version>
<externalTypeDefinitions><name>external</name>
<typeDefinitionsRef vendor="v" library="l" name="external-types" version="1"/>
</externalTypeDefinitions></typeDefinitions>''',
        TypeDefinitions,
    )
    external = definitions.external_type_definitions[0]
    type_ref_id = instantiation.getExternalTypeDefinitionsTypeDefinitionsRefID(get_handle(external))
    assert resolve_handle(type_ref_id).name == "external-types"

    root = component_document("shared")
    instantiation_id = component.getComponentComponentInstantiationIDs(get_handle(root))[0]
    file_ref_id = instantiation.getComponentInstantiationFileSetRefIDs(instantiation_id)[0]
    assert instantiation.getFileSetRefLocalName(file_ref_id) == "shared"

    chain = parse(
        f'''<generatorChain xmlns="{NS}"><vendor>v</vendor><library>l</library><name>chain</name><version>1</version>
<generatorChainSelector><generatorChainRef vendor="v" library="l" name="selected" version="1"/></generatorChainSelector>
</generatorChain>''',
        GeneratorChain,
    )
    selector = chain.generator_chain_selector_or_component_generator_selector_or_generator[0]
    chain_ref_id = instantiation.getGeneratorChainSelectorGeneratorChainRefID(get_handle(selector))
    assert resolve_handle(chain_ref_id).name == "selected"

    with pytest.raises(TgiError) as wrong:
        instantiation.getFileSetRefLocalName(type_ref_id)
    assert wrong.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as invalid:
        instantiation.getGeneratorChainSelectorGeneratorChainRefID("unknown")
    assert invalid.value.fault_code == TgiFaultCode.INVALID_ID


def test_design_ref_setters_validate_atomically_and_keep_parsed_handle_lifetime():
    root = component_document()
    instances = instantiations_of(root)
    design_inst, dci = instances[1], instances[2]
    design_inst_id, dci_id = get_handle(design_inst), get_handle(dci)
    design_ref_id = instantiation.getDesignInstantiationDesignRefID(design_inst_id)
    dci_ref_id = instantiation.getDesignConfigurationInstantiationDesignConfigurationRefID(dci_id)

    with pytest.raises(TgiError) as invalid_design:
        instantiation.setDesignInstantiationDesignRef(design_inst_id, ("v", "l", "", "2"))
    assert invalid_design.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert instantiation.getDesignInstantiationDesignRefByVLNV(design_inst_id) == ("v", "l", "design", "1")
    with pytest.raises(TgiError) as invalid_dc:
        instantiation.setDesignConfigurationInstantiationDesignConfigurationRef(dci_id, None)
    assert invalid_dc.value.fault_code == TgiFaultCode.INVALID_ARGUMENT

    assert instantiation.setDesignInstantiationDesignRef(design_inst_id, ("v2", "l2", "new-design", "2"))
    assert instantiation.getDesignInstantiationDesignRefID(design_inst_id) == design_ref_id
    assert resolve_handle(design_ref_id).name == "new-design"
    assert instantiation.setDesignConfigurationInstantiationDesignConfigurationRef(dci_id, ("v2", "l2", "new-dc", "2"))
    assert instantiation.getDesignConfigurationInstantiationDesignConfigurationRefID(dci_id) == dci_ref_id
    assert resolve_handle(dci_ref_id).name == "new-dc"

    loaded = XmlDocument.parser().from_string(XmlDocument.serializer().render(root), Component)
    loaded_instances = instantiations_of(loaded)
    loaded_design_id, loaded_dci_id = get_handle(loaded_instances[1]), get_handle(loaded_instances[2])
    assert instantiation.getDesignInstantiationDesignRefByVLNV(loaded_design_id) == ("v2", "l2", "new-design", "2")
    assert instantiation.getDesignConfigurationInstantiationDesignConfigurationRefByVLNV(loaded_dci_id) == (
        "v2", "l2", "new-dc", "2"
    )


def test_same_named_file_set_refs_remain_scoped_to_their_parsed_owner():
    roots = [component_document("same"), component_document("same")]
    inst_ids = [component.getComponentComponentInstantiationIDs(get_handle(root))[0] for root in roots]
    ref_ids = [instantiation.getComponentInstantiationFileSetRefIDs(handle)[0] for handle in inst_ids]
    assert ref_ids[0] != ref_ids[1]
    assert all(instantiation.getFileSetRefLocalName(handle) == "same" for handle in ref_ids)
    assert instantiation.removeComponentInstantiationFileSetRef(ref_ids[0])
    assert resolve_handle(ref_ids[0]) is None
    assert instantiation.getFileSetRefLocalName(ref_ids[1]) == "same"
