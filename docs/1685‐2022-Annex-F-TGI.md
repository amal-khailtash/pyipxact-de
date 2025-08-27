# Annex F

(normative)

Tight generator interface

IP-XACT generators are tools that are invoked from within a DE to perform an operation required by the
user of the DE. For example, generators can be provided to verify the configuration of a subsystem, generate
an address map, or write a netlist representation of the subsystem in a target language such as Verilog or
SystemC. To perform their various operations, most generators need access to the IP-XACT meta-data
describing the subsystem, as currently loaded into the DE. Generators need both read- and write-access to
the IP-XACT meta-data. All generators are external applications running in a separate address space from
the DE.

The TGI defines how the DE and generator cooperate to achieve the desired end-goal of the user of the DE.
The TGI defines the method of communication between the DE and generator, the method for invoking the
generator, and the actual application programming interface (API) that can be used to read and write the IP-
XACT meta-data stored in the DE. [F.1](#f.1_method_of_communication), [F.2](#f.2_generator_invocation),
and [F.3](#f.3_tgi_api) describe each of these three aspects of the TGI, respectively.

## F.1 Method of communication

The DE and the generator communicate with each other by sending messages to each other utilizing the
SOAP standard. SOAP or REST provides a simple means for sending XML-format messages using HTTP
or other transport protocols. The TGI restricts the set of allowed transport protocols to HTTP and a file-
based protocol. All generators are required to support HTTP, but support for the file-based protocol is
optional. The same rules apply to the DE—it shall support the use of HTTP, but is not required to support
the file-based protocol, even though a generator may allow it. The protocols supported by a generator are
specified using the transportMethod element within the componentGenerator element.

The information required to use a particular transport protocol shall be passed to the generator by the DE
when it is invoked, as described in [F.2](#f.2_generator_invocation). For HTTP, the generator is passed a URL of the form http://
host_name:port_number. All SOAP or REST messages sent to the DE shall be sent using the referenced
URL. For the file-based protocol, the generator is passed a URL of the form file://file_name. In this case, all
SOAP or REST messages are written to the specified file.

Each DE and generator is responsible for setting itself up to communicate using SOAP or REST with the
appropriate transport protocol. For example, a generator written in Tcl might include the Tcl SOAP package
to enable SOAP functionality. Once the communication channel is set up, the generator can read and write
the IP-XACT meta-data using any legal SOAP message. The set of legal SOAP and REST messages defines
the API portion of the TGI (see [F.7](#f.1_tgi_calls)).

## F.2 Generator invocation

All of the information known by the DE about a particular generator comes from an instance of the
componentGenerator (see 6.16), abstractorGenerator (see 8.9), or generator (see 10.4) elements. These
elements provides the following information:

a) name: The name of the generator as seen within the DE.
b) executable: The URL defining the location of the generator.
c) parameters: A list of name/value pairs defining information to be passed to the generator.
d) apiType: The generator type (TGI or none for no communication).
e) transportMethods: Transport mechanisms supported (in addition to mandatory HTTP).
f) phase: Not relevant to the TGI.
g) vendorExtensions: Not relevant to the TGI.
h) group: Not relevant to the TGI.

### F.2.1 Resolving the URL

The URL defining the generator executable shall resolve to one of the following forms:

— file:path_to_executable (e.g., file:/usr/jdoe/bin/mygen.pl or file:../bin/ mygen.pl) defines the path for invoking the generator on the machine from which the DE was invoked.
— file://machine_name/path_to_executable (e.g., file://server1/tmp/othergen.pl) defines the path for invoking a generator on the specified machine.
— http://web_address:port_number (e.g., http://www.acme.com/generator:1500) defines

the URL of a generator implemented as a Web-based server.

All file references are relative to the location of the XML description in which the file reference is
contained.

For the file-based generators, the DE shall invoke the generator as a sub-process with a command line built up as:

  executable -url transport_URL generator_parameter_arguments

The generator_parameter_arguments are the parameters from the componentGenerator element with the
user-specified values. Each parameter causes two additional arguments to be passed to the generator with
the following format: -parameter_name parameter_value. The DE needs to create a transport_URL that
specifies a protocol supported by the generator as defined by the transport methods within the
componentGenerator. The DE is also responsible for ensuring any passed parameters can be interpreted
correctly. This URL is to be used in the generator to set up the SOAP or REST communication channel.

For Web-based generators, the DE shall send a message to the address and port defined as the executable.
The format of this message is

  url=transport_URL&generator_parameter_arguments

In this case, the generator parameters are formatted using the standard HTTP parameter passing syntax. The
specified transport URL shall be used by the generator for any return messages to the DE.

The invocation syntax described above applies only to generators with an API type of TGI. Generators with
an API type of none are invoked as described above, excluding the transport_URL argument.

### F.2.2 Example

This example shows file-based and Web-based componentGenerator elements.

```xml
<ipxact:componentGenerator>
 <ipxact:name>myGenerator</ipxact:name>
 <ipxact:parameters>
  <ipxact:parameter resolve="user" parameterId="param1_id">
   <ipxact:name>param1</ipxact:name>
   <ipxact:value>"default1"</ipxact:value>
  </ipxact:parameter>
  <ipxact:parameter>
   <ipxact:name>param2</ipxact:name>
   <ipxact:value>"fixedValue"</ipxact:value>
  </ipxact:parameter>
 </ipxact:parameters>
 <ipxact:apiType>TGI_2022_BASE</ipxact:apiType>
 <ipxact:transportMethods>
  <ipxact:transportMethod>file</ipxact:transportMethod>
 </ipxact:transportMethods>
 <ipxact:generatorExe>../bin/myGenerator.pl</ipxact:generatorExe>
</ipxact:componentGenerator>
```

produces the following output:

  path_to _XML/../bin/myGenerator -url http://host:port -param1 default1

-param2 fixedValue

Whereas:

```xml
<ipxact:componentGenerator>
 <ipxact:name>myWebGenerator</ipxact:name>
  <ipxact:parameters>
   <ipxact:parameter resolve="user" parameterId="param1_id">
    <ipxact:name>param1</ipxact:name>
    <ipxact:value>"default1"</ipxact:value>
   </ipxact:parameter>
   <ipxact:parameter>
    <ipxact:name>param2</ipxact:name>
    <ipxact:value>"fixedValue"</ipxact:value>
   </ipxact:parameter>
  </ipxact:parameters>
 <ipxact:apiType>TGI_2022_BASE</ipxact:apiType>
 <ipxact:generatorExe>http://www.acme.com:1500</ipxact:generatorExe>
</ipxact:componentGenerator>
```

produces the following output:

  http://www.acme.com:1500?url=http%3a%2f%2fhost%3aport&param1=default1&param2=fixedValue

## F.3 TGI API

The TGI API defines the set of legal SOAP or REST messages that can be sent from a generator to a DE,
along with the format of the responses the generator can expect from a given request (message) to the DE.


The API shall provide the means of getting and setting values within the IP-XACT design currently
represented in the DE. The API commands can be classified as shown in Table F1.

Table F1—TGI API classifications

Classification    | Description | Example
|-----------------|-------------|-----------------|
| Administrative  | Commands that do not deal directly with the IP-XACT meta-data.                                 | Terminate communication.
| Traversal       | Commands that return a list of elements, which can then be traversed for further manipulation. | Get components in a design.
| Create          | Commands that create new top elements. These commands are only available in the TGI Extended mode. Create a new component.
| Add             | Commands that add a child element to a parent element. These commands are only available in the TGI Extended mode. | Add a busInterface to a component.
| Remove          | Commands that remove an element from its parent element. These commands are only available in the TGI Extended mode. | Remove a busInterface from a component.
| Get             | Commands that get attribute or element values. These com- mands are available for getting all information from the design and component schemas. If the attribute or element does not exist, this may return a default value, an empty string, or an empty array.                                     | Get port width.
| Set             | Commands that set element value or expression. If the element is not present, the set may create the element and assign it the given value. Set routines return a Boolean value where a true return code implies a successful operation. If false is returned, the SOAP or REST fault code shall provide additional information detailing the failure. | Set parameter value.

The complete set of API commands is defined using WSDL for the SOAP protocol or YAML for the REST
protocol, so that it can be defined in a language-independent format.

### F.3.1 TGI fault codes

The fault codes for TGI failures are as follows:

1 - Unknown (undefined) error
2 - Illegal element ID
3 - Illegal value(s)
4 - Element is not modifiable (incompatible resolve value)
5 - Operation not supported by the DE
6 - Operation not supported in this version of the schema
7 - Operation failed

### F.3.2 Administrative commands

There are three administrative commands defined in the API.

a) **Init** is the required first message from the generator to the DE. It tells the DE that the generator has
properly connected via the specified communication protocol (SOAP or REST).
    1) **Input**
        i) **apiVersion** of type string—Indicates the API version with which the generator is defined to work.
        ii) **failureMode** of type **apiFailureMode** — Compatibility failure mode
            **fail** indicates the DE shall return an error on the init call if its API version does not match the one passed to the init call;
            **error** indicates the DE shall return an error each time a potentially incompatible API call is made;
            **warning** indicates the DE shall increment a warning count each time a potentially incompatible API call is made.
        iii) **message** of type string—Message that the DE may display to the user.
    2) Returns: status of type boolean.
b) End is the required last message from the generator to the DE. It tells the DE it is okay to stop
listening for messages from the generator. This includes a generator return status, although the
generator is not strictly required to terminate after sending the message.
c) Message indicates some form of generator status to pass to the user.

### F.3.3 Return values

The TGI commands can return values of the following types:

— Boolean
— String
— List of Strings
— Long
— Double
— Float

Each basic type includes value NULL, which may be returned in case a value that is asked for is not defined.

## F.4 IDs and configurable values

The handles in TGI are classified as **instanceID**s and **ID**s. The **instanceID**s reference configured entities while the IDs reference unconfigured entities. The following TGI calls show the difference between **instanceID** and **ID** explicitly for top-level elements and configurable elements:

```
instanceID = abstractionDefInstanceID
      | busDefInstanceID
      | componentInstanceID
      | abstractorInstanceID
      | designInstanceID
      | designConfigurationInstanceID
      | typeDefinitionsInstanceID
```

```
ID = abstractionDefID
  | busDefID
  | componentID
  | abstractorID
  | designID
  | designConfigurationID
  | generatorChainID
  | typeDefinitionsID
```

For each instanceID, the getUnconfiguredID(instanceID) can be called to retrieve the ID. For the calls that
retrieve information (get calls), it is presumed the call on an instanceID also returns instanceIDs, e.g.,
getComponentBusInterfaceIDs(componentInstanceID) returns busInterfaceInstanceIDs (configured),
whereas getComponentBusInterfaceIDs(componentID) returns busInterfaceIDs (unconfigured). For
clarity, the distinction betweeninstanceIDs and IDs has not been made for non-top-level elements. Calls that
modify information (edit or set calls), operate only on IDs (unconfigured), e.g.,
addComponentInitiatorBusInterface(componentID) returns a new unconfigured busInterfaceID,
whereas the call addComponentInitiatorBusInterface(componentInstanceID) fails.

Handles returned by TGI commands are persistent for the duration of a single generator invocation provided
the element being referenced is not removed. For example, if a handle represents an address space element,
that handle can be utilized as often as is needed during a single generator invocation, unless the component
containing the address map is removed via removeDesignComponentInstance(). Furthermore, persistent
TGI handles to the same object are identical for the duration of the generator invocation. This enables
generators to identify objects by means of their handles.

## F.5 TGI messages

The TGI is a set of messages used to query and modify an IP-XACT–compliant database. For the SOAP
protocol, the TGI messages are composed of an envelope and a TGI body. The TGI services are specified in
the TGI.wsdl file. Each TGI body message is an XML element whose name is the name of the TGI
command and whose elements are the arguments of the TGI command. All TGI messages apply to IP-
XACT XML elements, identified by an ID, i.e., a TGI server-defined constant uniquely identifying an IP-
XACT XML element throughout a TGI server session.

## F.6 Vendor attributes

One case of special interest to a user may be the location of vendor attributes in the schema. These attributes
are allowed in more places in the schema than the TGI allows a user to retrieve them; this goes back to the
concept where one function uses many different ID types to return some data. Regardless, vendor attributes
can be accessed only if the containing element has an ID.

## F.7 TGI calls

This subclause details the TGI API calls. F.7.1 is an index of the various categories, and F.7.2 is an index for
the specific messages within each of those categories. The actual API breakouts start with subclause F.7.3.

### F.7.1 Category index

| Base category name            | Extended category name            |
|-------------------------------|-----------------------------------|
| Abstraction definition (BASE) | Abstraction definition (EXTENDED) |
| Abstractor (BASE)             | Abstractor (EXTENDED)             |
| Access handle (BASE)          | Access handle (EXTENDED)          |
| Access policy (BASE)          | Access policy (EXTENDED)          |
| Address space (BASE)          | Address space (EXTENDED)          |
| Array (BASE)                  | Array (EXTENDED)                  |
| Assertion (BASE)              | Assertion (EXTENDED)              |
| Bus definition (BASE)         | Bus definition (EXTENDED)         |
| Bus interface (BASE)          | Bus interface (EXTENDED)          |
| Catalog (BASE)                | Catalog (EXTENDED)                |
| Choice (BASE)                 | Choice (EXTENDED)                 |
| Clearbox (BASE)               | Clearbox (EXTENDED)               |
| Component (BASE)              | Component (EXTENDED)              |
| Configurable element (BASE)   | Configurable element (EXTENDED)   |
| Constraint (BASE)             | Constraint (EXTENDED)             |
| Constraint Set (BASE)         | Constraint Set (EXTENDED)         |
| CPU (BASE)                    | CPU (EXTENDED)                    |
| Design (BASE)                 | Design (EXTENDED)                 |
| Design configuration (BASE)   | Design configuration (EXTENDED)   |
| Driver (BASE)                 | Driver (EXTENDED)                 |
| Element attribute (BASE)      | Element attribute (EXTENDED)      |
| File builder (BASE)           | File builder (EXTENDED)           |
| File set (BASE)               | File set (EXTENDED)               |
| Generator (BASE)              | Generator (EXTENDED)              |
| Generator chain (BASE)        | Generator chain (EXTENDED)        |
| Indirect interface (BASE)     | Indirect interface (EXTENDED)     |
| Instantiation (BASE)          | Instantiation (EXTENDED)          |
| Memory map (BASE)             | Memory map (EXTENDED)             |
| Miscellaneous (BASE)          | Miscellaneous (EXTENDED)          |
| Module parameter (BASE)       | Module parameter (EXTENDED)       |
| Name group (BASE)             | Name group (EXTENDED)             |
| Parameter (BASE)              | Parameter (EXTENDED)              |
| Port (BASE)                   | Port (EXTENDED)                   |
| Port map (BASE)               | Port map (EXTENDED)               |
| Power (BASE)                  | Power (EXTENDED)                  |
| Register (BASE)               | Register (EXTENDED)               |
| Register file (BASE)          | Register file (EXTENDED)          |
| Slice (BASE)                  | Slice (EXTENDED)                  |
| Top element (BASE)            | Top element (EXTENDED)            |
| Type definitions (BASE)       | Type definitions (EXTENDED)       |
| Vector (BASE)                 | Vector (EXTENDED)                 |
| Vendor extensions (BASE)      | Vendor extensions (EXTENDED)      |
| View (BASE)                   | View (EXTENDED)                   |

### F.7.2 Abstraction definition (BASE)

#### F.7.2.1 getAbstractionDefBusTypeRefByVLNV

Description: Returns the busType VLNV defined on the given abstractionDef or abstractionDefInstance
element.

— Returns: VLNV of type String - The VLNV of the referenced busDefinition object
— Input: absDefOrAbsDefInstanceID of type String - Handle to an abstractionDef or abstractionDefInstance element

#### F.7.2.2 getAbstractionDefChoiceIDs

Description: Returns the handles to all the choices defined on the given abstraction definition object
element.

— Returns: choiceIDs of type String - List of handles to choice elements
— Input: abstractionDefinitionID of type String - Handle to an abstraction definition object element

#### F.7.2.3 getAbstractionDefExtendsRefByVLNV

Description: Returns the extended VLNV defined on the given abstractionDefinition object.

— Returns: VLNV of type String - The VLNV of the extended abstractionDefinition object
— Input: abstractionDefinitionID of type String - Handle to an abstractionDefinition object

#### F.7.2.4 getAbstractionDefPortIDs

Description: Returns the handles to all the ports defined on the given abstractionDefinition object.

— Returns: portIDs of type String - List of handles to the ports elements
— Input: abstractionDefinitionID of type String - Handle to an abstractionDefinition object

#### F.7.2.5 getAbstractionDefPortLogicalName

Description: Returns the logicalName element defined on the given abstractionDefPort element.

— Returns: logicalName of type String - The logical port name
— Input: abstractionDefPortID of type String - Handle to an abstractionDefPort element

#### F.7.2.6 getAbstractionDefPortMatch

Description: Returns the match of the given abstractionDefPort element.

— Returns: match of type Boolean - The logical port match
— Input: abstractionDefPortID of type String - Handle to abstractionDefPort element

#### F.7.2.7 getAbstractionDefPortOnSystemIDs

Description: Returns the handles to all the onSystem elements defined on the given abstractionDefPort
element.

— Returns: onSystemIDs of type String - List of handles to the onSystem elements
— Input: abstractionDefPortID of type String - Handle to abstractionDefPort element

#### F.7.2.8 getAbstractionDefPortPacketIDs

Description: Returns the handles to all the portPackets defined on the given abstractionDef port element.

— Returns: portPacketIDs of type String - List of portPacketType handles
— Input: abstractionDefPortID of type String - Handle to an abstractionDefinition port element

#### F.7.2.9 getAbstractionDefPortStyle

Description: Returns the port mode element defined on the given abstractionDefPort element.

— Returns: mode of type String - The logical port mode (onInitiator, onTarget, onSystem)
— Input: abstractionDefPortModeID of type String - Handle to an abstractionDefPort element

#### F.7.2.10 getAbstractionDefPortTransactionalModeBusWidth

Description: Returns the busWidth value defined on the given abstractionDef port element.

— Returns: busWidth of type Long - The port busWidth value
— Input: abstractionDefPortModeID of type String - Handle to a logical port transactional element

#### F.7.2.11 getAbstractionDefPortTransactionalModeBusWidthExpression

Description: Returns the busWidth expression defined on the given abstractionDef port element.

— Returns: busWidth of type String - The port busWidth expression
— Input: abstractionDefPortModeID of type String - Handle to a logical port transactional element

#### F.7.2.12 getAbstractionDefPortTransactionalModeBusWidthID

Description: Returns the handle to the busWidth defined on the given abstractionDef port element.

— Returns: busWidthID of type String - Handle to the busWidth element
— Input: abstractionDefPortModeID of type String - Handle to a logical port transactional element

#### F.7.2.13 getAbstractionDefPortTransactionalModeInitiative

Description: Returns the value of the initiative element defined on the given abstractionDef port element.

— Returns: initiative of type String - The port initiative
— Input: abstractionDefPortModeID of type String - Handle to a logical port transactional element

#### F.7.2.14 getAbstractionDefPortTransactionalModeKindID

Description: Returns the handle to the kind defined on the given abstractionDef port element.

— Returns: kindID of type String - Handle to the kind element
— Input: abstractionDefPortModeID of type String - Handle to a logical port transactional element

#### F.7.2.15 getAbstractionDefPortTransactionalModePresence

Description: Returns the value of the presence element defined on the given abstractionDef port element.

— Returns: presence of type String - The port presence
— Input: abstractionDefPortModeID of type String - Handle to a logical port transactional element

#### F.7.2.16 getAbstractionDefPortTransactionalModeProtocolID

Description: Returns the handle to the protocol defined on the given abstractionDef port element.

— Returns: protocolID of type String - Handle to the protocol element
— Input: abstractionDefPortModeID of type String - Handle to a logical port transactional element

#### F.7.2.17 getAbstractionDefPortTransactionalOnInitiatorID

Description: Returns the handle to the onInitiator element defined on the given abstractionDefinition port
transactional element.

— Returns: onInitiatorID of type String - Handle to the onInitiator element
— Input: abstractionDefPortID of type String - Handle to a transactional port element

#### F.7.2.18 getAbstractionDefPortTransactionalOnSystemIDs

Description: Returns the handles to all the onSystem elements defined on the given abstractionDef port
transactional element.

— Returns: onSystemIDs of type String - List of handles to the onSystem elements
— Input: abstractionDefPortID of type String - Handle to a logical port transactional element

#### F.7.2.19 getAbstractionDefPortTransactionalOnTargetID

Description: Returns the handle to the onTarget element defined on the given abstractionDefinition port
transactional element.

— Returns: onTargetID of type String - Handle to the onTarget element
— Input: abstractionDefPortID of type String - Handle to a transactional port element

#### F.7.2.20 getAbstractionDefPortTransactionalQualifierID

Description: Returns the handle to the qualifier defined on the given abstractionDef port transactional
element.

— Returns: qualifierID of type String - Handle to the qualifier element
— Input: portID of type String - Handle to a port element

#### F.7.2.21 getAbstractionDefPortWireDefaultValue

Description: Returns the defaultValue defined on the given abstractionDef logical port element.

— Returns: value of type Long - The logical port default value
— Input: abstractionDefPortID of type String - Handle to abstractionDefPort element

#### F.7.2.22 getAbstractionDefPortWireDefaultValueExpression

Description: Returns the defaultValue expression defined on the given abstractionDef logical port element.

— Returns: expression of type String - The logical port defaultValue expression
— Input: abstractionDefPortID of type String - Handle to abstractionDefPort element

#### F.7.2.23 getAbstractionDefPortWireDefaultValueID

Description: Returns the handle to the defaultValue defined on the given abstractionDef port element.

— Returns: defaultValueID of type String - Handle to the defaultValue element
— Input: abstractionDefPortModeID of type String - Handle to a logical port wire element

#### F.7.2.24 getAbstractionDefPortWireModeDirection

Description: Returns the direction defined on the given abstractionDef port element.

— Returns: direction of type String - The port direction
— Input: abstractionDefPortModeID of type String - Handle to a logical port wire element

#### F.7.2.25 getAbstractionDefPortWireModeMirroredModeConstraintsID

Description: Returns the handle to the mirroredModeConstraints defined on the given abstractionDef port
element.

— Returns: mirroredModeConstraintsID of type String - Handle to the mirroredModeConstraints element
— Input: abstractionDefPortModeID of type String - Handle to a logical port wire element

#### F.7.2.26 getAbstractionDefPortWireModeModeConstraintsID

Description: Returns the handle to the modeConstraints defined on the given abstractionDef port element.

— Returns: modeConstraintsID of type String - Handle to the modeConstraints element
— Input: abstractionDefPortModeID of type String - Handle to a logical port wire element

#### F.7.2.27 getAbstractionDefPortWireModePresence

Description: Returns the presence defined on the given abstractionDef port element.

— Returns: presence of type String - The presence value
— Input: abstractionDefPortModeID of type String - Handle to a logical port wire element

#### F.7.2.28 getAbstractionDefPortWireModeWidth

Description: Returns the width value defined on the given abstractionDef port element.

— Returns: width of type Long - The width value
— Input: portModeID of type String - Handle to a logical port wire element

#### F.7.2.29 getAbstractionDefPortWireModeWidthExpression

Description: Returns the width expression defined on the given abstractionDef port element.

— Returns: width of type String - The width expression
— Input: portModeID of type String - Handle to a logical port wire element

#### F.7.2.30 getAbstractionDefPortWireModeWidthID

Description: Returns the handle to the width defined on the given abstractionDef port element.

— Returns: widthID of type String - Handle to the width element
— Input: portModeID of type String - Handle to a logical port wire element

#### F.7.2.31 getAbstractionDefPortWireOnInitiatorID

Description: Returns the handle to the onInitiator element defined on the given abstractionDef port element.

— Returns: onInitiatorID of type String - Handle to the onInitiator element
— Input: abstractionDefPortModeID of type String - Handle to a logical port wire element

#### F.7.2.32 getAbstractionDefPortWireOnSystemIDs

Description: Returns the handles to all the onSystem elements defined on the given abstractionDef port wire
element.

— Returns: onSystemIDs of type String - List of handles to the onSystem elements
— Input: portID of type String - Handle to a logical port wire element

#### F.7.2.33 getAbstractionDefPortWireOnTargetID

Description: Returns the handle to the onTarget defined on the given abstractionDef port.

— Returns: onTargetID of type String - Handle to the onTarget element
— Input: abstractionDefPortID of type String - Handle to a logical port wire element

#### F.7.2.34 getAbstractionDefPortWireQualifierID

Description: Returns the handle to the qualifier defined on the given abstractionDef port wire element.

— Returns: qualifierID of type String - Handle to the qualifier element
— Input: portID of type String - Handle to a port element

#### F.7.2.35 getAbstractionDefPortWireRequiresDriver

Description: Returns the requiresDriver element defined on the given abstractionDefPort element.

— Returns: value of type Boolean - The logical port requiresDriver value
— Input: abstractionDefPortID of type String - Handle to an abstractionDefPort element

#### F.7.2.36 getAbstractionDefPortWireRequiresDriverID

Description: Returns the handle to the requiresDriver defined on the given abstractionDefPort element.

— Returns: requiresDriverID of type String - Handle to the requiresDriver element
— Input: abstractionDefPortModeID of type String - Handle to a logical port wire element

#### F.7.2.37 getModeConstraintsDriveConstraintCellSpecificationID

Description: Returns the handle to the driveConstraint defined on the given modeConstraints element.

— Returns: driveConstraintID of type String - Handle to the driveConstraint element
— Input: modeConstraintsID of type String - Handle to a modeConstraints element

#### F.7.2.38 getModeConstraintsLoadConstraintID

Description: Returns the handle to the loadConstraint defined on the given modeConstraints element.

— Returns: loadConstraintID of type String - Handle to the loadConstraint element
— Input: modeConstraintsID of type String - Handle to a modeConstraints element

#### F.7.2.39 getModeConstraintsTimingConstraintIDs

Description: Returns the handles to all the timingConstraints defined on the given modeConstraints element.

— Returns: timingConstraintIDs of type String - List of handles to the timingConstraint elements
— Input: modeConstraintsID of type String - Handle to a modeConstraints element

#### F.7.2.40 getOnSystemGroup

Description: Returns the group attribute defined the given onSystem element.

— Returns: group of type String - The group name
— Input: onSystemID of type String - Handle to an onSystem element

#### F.7.2.41 getPacketEndianness

Description: Returns the endianness defined on the given packet element.

— Returns: endianness of type String - The endianness (big or little)
— Input: packetID of type String - Handle to a packet element

#### F.7.2.42 getPacketFieldEndianness

Description: Returns the endianness defined on the given packetField element.

— Returns: endianness of type String - The endianness (big or little)
— Input: packetFieldID of type String - Handle to a packetField element

#### F.7.2.43 getPacketFieldQualifierID

Description: Returns the handle to the qualifier defined on the given packetField element.

— Returns: qualifierID of type String - Handle to the qualifier element
— Input: packetFieldID of type String - Handle to a packetFied element

#### F.7.2.44 getPacketFieldValue

Description: Returns the (resolved) value of the value element defined on the given packetField element.

— Returns: value of type Long - The value of the value element
— Input: packetFieldID of type String - Handle to a packetField element

#### F.7.2.45 getPacketFieldValueExpression

Description: Returns the expression defined on the value element of the given packetField element.

— Returns: valueExpression of type String - The expression defined on the value element
— Input: packetFieldID of type String - Handle to a packetField element

#### F.7.2.46 getPacketFieldValueID

Description: Returns the handle to the value element defined on the given packetField element.

— Returns: valueID of type String - Handle to the value element
— Input: packetFieldID of type String - Handle to a packetField element

#### F.7.2.47 getPacketFieldWidth

Description: Returns the (resolved) width value defined on the given packetField element.

— Returns: width of type Long - The value of the width element
— Input: packetFieldID of type String - Handle to a packetField element

#### F.7.2.48 getPacketFieldWidthExpression

Description: Returns the width expression defined on the given packetField element.

— Returns: width of type String - The width expression
— Input: packetFieldID of type String - Handle to a packetField element

#### F.7.2.49 getPacketFieldWidthID

Description: Returns the handle to the width element defined on the given packetField element.

— Returns: widthID of type String - Handle to the width element
— Input: packetFieldID of type String - Handle to a packetField element

#### F.7.2.50 getPacketPacketFieldIDs

Description: Returns the handles to all the packetFields defined on the given packet element.

— Returns: packetFieldIDs of type String - List of handles to packetField elements
— Input: packetID of type String - Handle to a packet element

### F.7.3 Abstraction definition (EXTENDED)

#### F.7.3.1 addAbstractionDefChoice

Description: Adds a choice with the given name and enumerations to the given abstraction definition
element.

— Returns: choiceID of type String - Handle to a new choice
— Input: abstractionDefinitionID of type String - Handle to an abstraction definition element
— Input: name of type String - Choice name
— Input: enumerations of type String[] - List of enumeration values

#### F.7.3.2 addAbstractionDefPort

Description: Adds abstractionDefPort with the given logicalName and type to the given abstractionDef
element.

— Returns: abstractionDefPortID of type String - Handle to a new abstractionDefPort element
— Input: abstractionDefID of type String - Handle to an abstractionDef element
— Input: logicalName of type String - Logical port name
— Input: type of type String - Logical port style (wire or transactional)

#### F.7.3.3 addAbstractionDefPortMode

Description: Adds abstractionDefPortMode with the given value for the given abstractionDefPort element.

— Returns: abstractionDefPortModeID of type String - Handle to a new abstractionDefPortMode element
— Input: abstractionDefPortID of type String - Handle to abstractionDefPort element
— Input: mode of type String - Logical port mode (onInitiator, onTarget, onSystem)

#### F.7.3.4 addAbstractionDefPortPacket

Description: Adds a port packet to the given logical port element.

— Returns: portPacketTypeID of type String - Handle to the added portPacketType
— Input: absDefPortID of type String - Handle to an absDefPort element
— Input: packetName of type String - Name of the packet
— Input: packetFieldName of type String - Name of the packetField
— Input: packetFieldWidth of type String - Width of the packetField

#### F.7.3.5 addAbstractionDefPortTransactionalOnSystem

Description: Adds an onSystem element to the given port transactional.

— Returns: onSystemID of type String - Handle to the added OnSystem
— Input: portID of type String - Handle to a port element
— Input: group of type String - Group name

#### F.7.3.6 addAbstractionDefPortWireOnSystem

Description: Adds an onSystem to the given port element.

— Returns: onSystemID of type String - Handle to the added onSystem
— Input: portID of type String - Handle to a port element
— Input: group of type String - Group name

#### F.7.3.7 addModeConstraintsTimingConstraint

Description: Adds timingConstraint with the given type for the given abstractionDefPortMode element.

— Returns: timingConstraintID of type String - Handle to the added timingConstraint
— Input: modeConstraintsID of type String - Handle to modeConstraints element
— Input: value of type float - The timingConstraint value
— Input: clockName of type String - The timingConstraint clock name

#### F.7.3.8 addPacketPacketField

Description: Adds a packetField for the given packet element.

— Returns: packetFieldID of type String - Handle to the added PortPacketField
— Input: packetID of type String - Handle to a packet element
— Input: fieldName of type String - Name of the field created
— Input: width of type Long - Width of the field created

#### F.7.3.9 removeAbstractionDefChoice

Description: Removes the given choice element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: choiceID of type String - Handle to a choice element

#### F.7.3.10 removeAbstractionDefExtends

Description: Removes extends from the given abstractionDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefID of type String - Handle to an abstractionDef element

#### F.7.3.11 removeAbstractionDefPort

Description: Removes the given abstractionDefPort element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortID of type String - Handle to abstractionDefPort element

#### F.7.3.12 removeAbstractionDefPortMatch

Description: Removes match element from the given abstractionDefPort element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortID of type String - Handle to abstractionDefPort element

#### F.7.3.13 removeAbstractionDefPortMode

Description: Removes abstractionDefPortMode with the given abstractionDefPortModeID.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortModeID of type String - Handle to abstractionDefPortMode element

#### F.7.3.14 removeAbstractionDefPortTransactionalModeBusWidth

Description: Removes busWidth from the given abstractionDefPort element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortModeID of type String - Handle to abstractionDefPortMode element

#### F.7.3.15 removeAbstractionDefPortTransactionalModeInitiative

Description: Removes initiative from the given abstractionDefPort element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortModeID of type String - Handle to abstractionDefPort element

#### F.7.3.16 removeAbstractionDefPortTransactionalModeKind

Description: Removes kind from the given abstractionDefPort element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortModeID of type String - Handle to abstractionDefPort element

#### F.7.3.17 removeAbstractionDefPortTransactionalModePresence

Description: Removes presence from the given abstractionDefPortMode element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortModeID of type String - Handle to abstractionDefPortMode element

#### F.7.3.18 removeAbstractionDefPortTransactionalModeProtocol

Description: Removes protocol from the given abstractionDefPort element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortModeID of type String - Handle to abstractionDefPortMode element

#### F.7.3.19 removeAbstractionDefPortTransactionalOnInitiator

Description: Removes the onInitiator on an abstractionDefinition port transactional.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortID of type String - The identifier of a transactional abstractionDefinition port

#### F.7.3.20 removeAbstractionDefPortTransactionalOnSystem

Description: Removes the given onSystem element from its containing logical transactional port.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: onSystemID of type String - Handle to an onSystem element

#### F.7.3.21 removeAbstractionDefPortTransactionalOnTarget

Description: Removes the onTarget on an abstractionDefinition port transactional.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortID of type String - the identifier of a transactional abstractionDefinition port

#### F.7.3.22 removeAbstractionDefPortTransactionalQualifier

Description: Removes the given qualifier from its contained abstractDefinition port.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - Handle to qualifier

#### F.7.3.23 removeAbstractionDefPortWireDefaultValue

Description: Removes defaultValue from the given abstractionDefPort element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortID of type String - Handle to abstractionDefPort element

#### F.7.3.24 removeAbstractionDefPortWireModeDirection

Description: Removes direction from the given abstractionDefPortMode element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortModeID of type String - Handle to abstractionDefPortMode element

#### F.7.3.25 removeAbstractionDefPortWireModeMirroredModeConstraints

Description: Removes mirroredModeConstraints for the given abstractionDefPortMode element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortModeID of type String - Handle to abstractionDefPortMode element

#### F.7.3.26 removeAbstractionDefPortWireModeModeConstraints

Description: Removes modeConstraints for the given abstractionDefPortMode element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortModeID of type String - Handle to abstractionDefPortMode element

#### F.7.3.27 removeAbstractionDefPortWireModePresence

Description: Removes presence from the given abstractionDefPortMode element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortModeID of type String - Handle to abstractionDefPortMode element

#### F.7.3.28 removeAbstractionDefPortWireModeWidth

Description: Removes width from the given abstractionDefPortMode element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortModeID of type String - Handle to abstractionDefPortMode element

#### F.7.3.29 removeAbstractionDefPortWireOnInitiator

Description: Removes the onInitiator element from a wire abstractionDefinition port.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortID of type String - Handle to the abstractionDefPort element

#### F.7.3.30 removeAbstractionDefPortWireOnSystem

Description: Removes the onSystem element from its containing logical wire port.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: onSystemID of type String - Handle to an onSystem element

#### F.7.3.31 removeAbstractionDefPortWireOnTarget

Description: Removes the onTarget element from a wire abstractionDefinitionPort.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortID of type String - Handle to a logical port element

#### F.7.3.32 removeAbstractionDefPortWireQualifier

Description: Removes the given qualifier from a wire abstractionDefinitionPort.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - Handle to qualifier

#### F.7.3.33 removeAbstractionDefPortWireRequiresDriver

Description: Removes requiresDriver from a wire abstractionDefPort element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortID of type String - Handle to abstractionDefPort element

#### F.7.3.34 removeCustomAttribute

Description: Removes custom attribute of kind from the given abstractionDefPort element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortModeID of type String - Handle to abstractionDefPortMode element

#### F.7.3.35 removeMandatoryAttribute

Description: Removes mandatory attribute of payloadExtension from the given abstractionDefPort element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortModeID of type String - Handle to abstractionDefPort element

#### F.7.3.36 removeModeConstraintsDriveConstraint

Description: Removes driveConstraint with the given modeConstraints.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: modeConstraintsID of type String - Handle to modeConstraints element

#### F.7.3.37 removeModeConstraintsLoadConstraint

Description: Removes loadConstraint with the given modeConstraints.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: modeConstraintsID of type String - Handle to modeConstraints element

#### F.7.3.38 removeModeConstraintsTimingConstraint

Description: Removes timingConstraint with the given timingConstraintID.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: timingConstraintID of type String - Handle to timingConstraint element

#### F.7.3.39 removePacketEndianness

Description: Removes the endianness associated with the given packet element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: packetID of type String - Handle to a packet element

#### F.7.3.40 removePacketFieldEndianness

Description: Removes the endianness associated with the given packetField element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: packetFieldID of type String - Handle to a packetField element

#### F.7.3.41 removePacketFieldQualifier

Description: Removes the given qualifier from its contained packetField.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: packetFieldID of type String - Handle to packetField element

#### F.7.3.42 removePacketFieldValue

Description: Removes the value of the given packetField.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: packetFieldID of type String - Handle to a packetField element

#### F.7.3.43 removePacketPacketField

Description: Removes the given packetField from its containing packet element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: packetFieldID of type String - Handle to a packetField element

#### F.7.3.44 setAbstractionDefExtends

Description: Sets extends with the given value for the given abstractionDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefID of type String - Handle to an abstractionDef element
— Input: abstractionDefVLNV of type String[] - AbstractionDef VLNV

#### F.7.3.45 setAbstractionDefPortLogicalName

Description: Sets the logicalName to the given value for the given abstractionDefPort element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortID of type String - Handle to abstractionDefPort elemen
— Input: value of type String - new logical port name

#### F.7.3.46 setAbstractionDefPortMatch

Description: Sets match with the given value for the given abstractionDefPort element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortID of type String - Handle to abstractionDefPort element
— Input: match of type Boolean - match value

#### F.7.3.47 setAbstractionDefPortMode

Description: Sets the mode with the given value for the given abstractionDefPort element.

— Returns: modeID of type String - Handle of new created mode
— Input: abstractionDefPortID of type String - Handle to an abstractionDefPort element
— Input: mode of type String - mode value

#### F.7.3.48 setAbstractionDefPortTransactionalModeBusWidth

Description: Sets busWidth to the given abstractionDefPortMode element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortModeID of type String - Handle to abstractionDefPortMode ele- ment
— Input: width of type String - width expression

#### F.7.3.49 setAbstractionDefPortTransactionalModeInitiative

Description: Sets initiative for the given abstractionDefPortMode element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortModeID of type String - Handle to abstractionDefPortMode ele- ment
— Input: initiative of type String - initiative value. Can be one of 'requires', 'provides' or 'both'

#### F.7.3.50 setAbstractionDefPortTransactionalModeKind

Description: Sets kind for the given abstractionDefPortMode element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortModeID of type String - Handle to abstractionDefPortMode element
— Input: kind of type String - kind value. Can be one of 'tlm_port', 'tlm_socket', 'simple_socket', 'multi_socket', 'custom'

#### F.7.3.51 setAbstractionDefPortTransactionalModePresence

Description: Sets presence for the given abstractionDefPortMode element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortModeID of type String - Handle to abstractionDefPortMode element
— Input: presence of type String - presence value. Can be one of 'required', 'illegal' or 'optional'

#### F.7.3.52 setAbstractionDefPortTransactionalModeProtocol

Description: Sets protocol for the given abstractionDefPort element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortModeID of type String - Handle to abstractionDefPort element
— Input: protocolType of type String - the type of protocol. Can be one of 'tlm' or 'custom'

#### F.7.3.53 setAbstractionDefPortTransactionalOnInitiator

Description: Sets the onInitiator on an abstractionDefinition port transactional.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortID of type String - the identifier of a transactional abstractionDefinition port

#### F.7.3.54 setAbstractionDefPortTransactionalOnTarget

Description: Sets the onTarget on an abstractionDefinition port transactional.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortID of type String - the identifier of a transactional abstractionDefinition port

#### F.7.3.55 setAbstractionDefPortTransactionalQualifier

Description: Sets the qualifier on an abstractionDefinition port transactional.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: portID of type String - Handle to port

#### F.7.3.56 setAbstractionDefPortWire

Description: Set the wire element of an abstraction definition port.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortID of type String - Handle to abstraction definition port

#### F.7.3.57 setAbstractionDefPortTransactional

Description: Set the transactional element of an abstraction definition port.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortID of type String - Handle to abstraction definition port

#### F.7.3.58 setAbstractionDefPortWireDefaultValue

Description: Sets defaultValue with the given value for the given abstractionDefPort element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortID of type String - Handle to abstractionDefPort element
— Input: valueExpression of type String - Logical port default value

#### F.7.3.59 setAbstractionDefPortWireModeDirection

Description: Sets direction with the given value for the given abstractionDefPortMode element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortModeID of type String - Handle to abstractionDefPortMode element
— Input: direction of type String - Logical port direction

#### F.7.3.60 setAbstractionDefPortWireModeMirroredModeConstraints

Description: Sets mirroredModeConstraints element for the given abstractionDefPortMode element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortModeID of type String - Handle to abstractionDefPortMode element
— Input: timingConstraintClockName of type String - clockName of the timingConstraint

#### F.7.3.61 setAbstractionDefPortWireModeModeConstraints

Description: Sets modeConstraints for the given abstractionDefPortMode element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortModeID of type String - Handle to abstractionDefPortMode element
— Input: timingConstraintClockName of type String - clockName of the timingConstraint

#### F.7.3.62 setAbstractionDefPortWireModePresence

Description: Sets the presence on a wire port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: portModeID of type String - Handle to a portModeElement (onInitiator, onWire, onTarget)
— Input: presence of type String - the presence value

#### F.7.3.63 setAbstractionDefPortWireModeWidth

Description: Sets the width on a wire port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: portModeID of type String - Handle to a portModeElement (onInitiator, onWire, onTarget)
— Input: width of type String - the presence value

#### F.7.3.64 setAbstractionDefPortWireOnInitiator

Description: Sets the onInitiator on a wire abstractionDefinition port.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortID of type String - Handle to the abstractionDefPort

#### F.7.3.65 setAbstractionDefPortWireOnTarget

Description: Sets the onTarget element defined on the given logical port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortID of type String - Handle to a logical port element

#### F.7.3.66 setAbstractionDefPortWireQualifier

Description: Sets the qualifier on the given abstractDefinition port.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortID of type String - Handle to port

#### F.7.3.67 setAbstractionDefPortWireRequiresDriver

Description: Sets requiresDriver with the given value for the given abstractionDefPort element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefPortID of type String - Handle to abstractionDefPort element
— Input: value of type Boolean - Logical port requiresDriver value

#### F.7.3.68 setModeConstraintsDriveConstraint

Description: Adds driveConstraint with the given type for the given abstractionDefPortMode element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: modeConstraintsID of type String - Handle to modeConstraints element
— Input: cellType of type String - cellFunction or cellClass of the driveConstraint

#### F.7.3.69 setModeConstraintsLoadConstraint

Description: Adds loadConstraint with the given type for the given abstractionDefPortMode element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: modeConstraintsID of type String - Handle to modeConstraints element
— Input: cellType of type String - cellFunction or cellClass of the driveConstraint

#### F.7.3.70 setOnSystemGroup

Description: Sets the group on an onSystem element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: onSystemID of type String - Handle to an onSystem element
— Input: group of type String - The group value

#### F.7.3.71 setPacketEndianness

Description: Sets the endianness associated with the given packet element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: packetID of type String - Handle to a packet element
— Input: endianness of type String - Required endianness (“big” or “little”)

#### F.7.3.72 setPacketFieldEndianness

Description: Sets the endianness associated with the given packetField element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: packetFieldID of type String - Handle to a packetField element
— Input: endianness of type String - Required endianness (“big” or “little”)

#### F.7.3.73 setPacketFieldQualifier

Description: Sets the qualifier on the given packetField.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: packetFieldID of type String - Handle to packetFied

#### F.7.3.74 setPacketFieldValue

Description: Sets the value of the given packetField.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: packetFieldID of type String - Handle to a packetField element
— Input: expression of type String - The new value or expression

#### F.7.3.75 setPacketFieldWidth

Description: Sets the expression of the “width” field associated with the given packetField element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: packetFieldID of type String - Handle to a packetField element
— Input: expression of type String - Handle to the new value

### F.7.4 Abstractor (BASE)

#### F.7.4.1 getAbstractorAbstractorGeneratorIDs

Description: Returns the handles to the generators defined on the given abstractor or abstractorInstance
element.

— Returns: generatorIDs of type String - List of handles to the generator elements
— Input: abstractorOrAbstractorInstanceID of type String - Handle to an abstractor or abstractorInstance element

#### F.7.4.2 getAbstractorAbstractorInterfaceIDs

Description: Returns the handles to all the abstractorInterfaces defined on the given abstractor or
abstractorInstance element.

— Returns: abstractorBusInterfaceIDs of type String - List of abstractorBusInterface handles
— Input: abstractorID of type String - Handle to an abstractor object

#### F.7.4.3 getAbstractorAbstractorMode

Description: Returns the abstractorMode defined on the given abstractor object.

— Returns: mode of type String - The abstractorMode value
— Input: abstractorID of type String - Handle to an abstractor object

#### F.7.4.4 getAbstractorAbstractorModeID

Description: Returns the handle to the abstractorMode defined on the given abstractor element.

— Returns: abstractorModeID of type String - Handle to the abstractorMode element
— Input: abstractorID of type String - Handle to an abstractor element

#### F.7.4.5 getAbstractorBusTypeRefByVLNV

Description: Returns the busType VLNV defined on the given abstractor object.

— Returns: VLNV of type String - The VLNV of the referenced busDefinition object
— Input: abstractorID of type String - Handle to an abstractor object

#### F.7.4.6 getAbstractorChoiceIDs

Description: Returns the handles to all the choices defined on the given abstractor or abstractorInstance
element.

— Returns: choiceIDs of type String - List of handles to choice elements
— Input: abstractorID of type String - Handle to an abstractor object

#### F.7.4.7 getAbstractorComponentInstantiationIDs

Description: Returns the handles to all the componentInstantations defined on the given abstractor or
abstractorInstance element.

— Returns: componentInstantiationIDs of type String - List of handles to the componentInstantiation elements
— Input: abstractorOrAbstractorInstanceID of type String - Handle to an abstractor or abstractorInstance element

#### F.7.4.8 getAbstractorFileSetIDs

Description: Returns the handles to all the fileSets defined on the given abstractor or abstractorInstance
element.

— Returns: fileSetIDs of type String - List of handles to the fileSet elements
— Input: abstractorID of type String - Handle to an abstractor object

#### F.7.4.9 getAbstractorInterfaceAbstractionTypeIDs

Description: Returns the handles to all the abstractionTypes defined on the given abstractorInterface element
on an abstractor

— Returns: abstractionTypeIDs of type String - List of abstractionType handles
— Input: abstractorInterfaceID of type String - Handle to an abstractorInterface element

#### F.7.4.10 getAbstractorPortIDs

Description: Returns the handles to all the ports defined on the given abstractor or abstractorInstance
element.

— Returns: portIDs of type String - List of handles to the port elements
— Input: abstractorID of type String - Handle to an abstractor object

#### F.7.4.11 getAbstractorViewIDs

Description: Returns the handles to all the abstractorViews defined on the given abstractor or
abstractorInstance element.

— Returns: abstractorViewIDs of type String - List of handles to the abstractorView elements
— Input: abstractorID of type String - Handle to an abstractor object

### F.7.5 Abstractor (EXTENDED)

#### F.7.5.1 addAbstractorAbstractorGenerator

Description: Adds a generator with the given name and path to the given abstractor element.

— Returns: generatorID of type String - Handle to a new generator
— Input: abstractorID of type String - Handle to an abstractor element
— Input: name of type String - Generator name
— Input: generatorExecutable of type String - Path to generator executable

#### F.7.5.2 addAbstractorChoice

Description: Adds a choice with the given name and enumerations to the given abstractor element.

— Returns: choiceID of type String - Handle to a new choice
— Input: abstractorID of type String - Handle to an abstractor element
— Input: name of type String - Choice name
— Input: enumerations of type String[] - List of enumerations

#### F.7.5.3 addAbstractorComponentInstantiation

Description: Adds a componentInstantiation with the given name for the given abstractor element.

— Returns: componentInstantiationID of type String - Handle to a new componentInstantiation
— Input: abstractorID of type String - Handle to an abstractor element
— Input: name of type String - ComponentIntstantiation name

#### F.7.5.4 addAbstractorFileSet

Description: Adds a fileSet with the given name to the given abstractor element.

— Returns: fileSetID of type String - Handle to a new fileSet
— Input: abstractorID of type String - Handle to an abstractor element
— Input: name of type String - FileSet name

#### F.7.5.5 addAbstractorInterfaceAbstractionType

Description: Adds an abstractionType with the given abstractionRef for the given abstractorBusInterface
element.

— Returns: abstractionTypeID of type String - Handle to a new abstractionType
— Input: abstractorBusInterfaceID of type String - Handle to an abstractorBusInterface element
— Input: abstractionRef of type String[] - abstractionDef VLNV

#### F.7.5.6 addAbstractorStructuredInterfacePort

Description: Adds a structured port with the given name and directionOrInitiative for the given abstractor
element.

— Returns: portID of type String - Handle to a new port
— Input: abstractorID of type String - Handle to an abstractor element
— Input: name of type String - Handle to a port by his name
— Input: subPortName of type String - The name of the subPort
— Input: structPortTypeDefTypeName of type String - The typeName of the structPortTypeDef

#### F.7.5.7 addAbstractorStructuredStructPort

Description: Adds a structured struct port with the given name and direction for the given abstractor
element.

— Returns: portID of type String - Handle to a new port
— Input: abstractorID of type String - Handle to an abstractor element
— Input: name of type String - Handle to a port by his name
— Input: subPortName of type String - The name of the subPort
— Input: structPortTypeDefTypeName of type String - The typeName of the structPortTypeDef — Input: direction of type String - Value of the direction

#### F.7.5.8 addAbstractorStructuredUnionPort

Description: Adds a structured union port with the given name and direction for the given abstractor
element.

— Returns: portID of type String - Handle to a new port
— Input: abstractorID of type String - Handle to an abstractor element
— Input: name of type String - Handle to a port by his name
— Input: structPortTypeDefTypeName of type String - The typeName of the structPortTypeDef
— Input: subPortName of type String - The name of the subPort
— Input: direction of type String - Value of the direction

#### F.7.5.9 addAbstractorTransactionalPort

Description: Adds a transactional port with the given name and initiative for the given abstractor element.

— Returns: portID of type String - Handle to a new port
— Input: abstractorID of type String - Handle to an abstractor element
— Input: name of type String - port name
— Input: initiative of type String - Port initiative

#### F.7.5.10 addAbstractorView

Description: Adds an abstractorView with the given name and envIdentifier for the given abstractor
element.

— Returns: abstractorViewID of type String - Handle to the added abstractorView
— Input: abstractorID of type String - Handle to an abstractor element
— Input: name of type String - Abstractor view name

#### F.7.5.11 addAbstractorWirePort

Description: Adds a wire port with the given name and direction for the given abstractor element.

— Returns: portID of type String - Handle to a new port
— Input: abstractorID of type String - Handle to an abstractor element
— Input: name of type String - port name
— Input: direction of type String - Port direction

#### F.7.5.12 removeAbstractorAbstractorGenerator

Description: Removes the given generator element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: generatorID of type String - Handle to a generator element

#### F.7.5.13 removeAbstractorAbstractorInterface

Description: Removes the given abstractorInterface.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractorInterfaceID of type String - Handle to an abstractorInterface element

#### F.7.5.14 removeAbstractorChoice

Description: Removes the given choice element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: choiceID of type String - Handle to a choice element

#### F.7.5.15 removeAbstractorComponentInstantiation

Description: Removes the given componentInstantiation element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

#### F.7.5.16 removeAbstractorFileSet

Description: Removes the given fileSet element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileSetID of type String - Handle to a fileSet element

#### F.7.5.17 removeAbstractorInterfaceAbstractionType

Description: Removes the given abstractionType element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionTypeID of type String - Handle to an abstractionType element

#### F.7.5.18 removeAbstractorPort

Description: Removes the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: portID of type String - Handle to a port element

#### F.7.5.19 removeAbstractorView

Description: Removes the given abstractorView element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractorViewID of type String - Handle to an abstractorView element

#### F.7.5.20 removeFileSetRefGroupFileSetRef

Description: Removes the given FileSetRef from its containing FileSetGroup element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileSetRefID of type String - Handle to a fileSetRef

#### F.7.5.21 setAbstractorAbstractorMode

Description: Sets the abstractorMode for the abstractor.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractorID of type String - Handle to an abstractor element
— Input: abstractorMode of type String - Mode name. Can be one of: initiator, target, direct or system

#### F.7.5.22 setAbstractorBusType

Description: Sets the busType of the abstractor.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractorID of type String - Handle to an abstractorType element
— Input: value of type String[] - The VLNV of the busType

### F.7.6 Access Policy (BASE)

#### F.7.6.1 getFieldAccessPolicyModeRefByID

Description: Returns the modeID defined on the given field access policy element.

— Returns: modeID of type String - Handle to the referenced mode element
— Input: fieldAccessPolicyID of type String - Handle to an field access policy element
— Input: modeRef of type String - Handle to the referenced modeRef element

### F.7.7 Access handle (BASE)

#### F.7.7.1 getAccessHandleForce

Description: Returns the value of the force attribute defined on the given accessHandle element.

— Returns: force of type Boolean - The value of the force attribute
— Input: accessHandleID of type String - Handle to an accessHandle element

#### F.7.7.2 getAccessHandleIDs

Description: Returns the handles to all the accesHandles defined on the given accessHandle element.

— Returns: accesHandleIDs of type String - List of handles to the accesHandle elements
— Input: elementID of type String - Handle to an element

#### F.7.7.3 getAccessHandleIndicesIDs

Description: Returns the handles to all the indices defined on the given accessHandle element.

— Returns: indicesID of type String - List of handles to the indices elements
— Input: accessHandleID of type String - Handle to an accessHandle element

#### F.7.7.4 getAccessHandlePathSegmentIDs

Description: Returns the handles to all the pathSegments defined on the given accessHandle element.

— Returns: pathSegmentIDs of type String - List of handles to the pathSegment elements
— Input: accessHandleID of type String - Handle to an accessHandle element

#### F.7.7.5 getAccessHandleSliceIDs

Description: Returns the handles to all the slides defined on the given accessHandle element.

— Returns: sliceIDs of type String - List of handles to the slice elements
— Input: accessHandleID of type String - Handle to an accessHandle element

#### F.7.7.6 getAccessHandleViewRefIDs

Description: Returns the handles to all the views defined on the given accessHandle element.

— Returns: viewIDs of type String - List of handles to the view elements
— Input: accessHandleID of type String - Handle to an accessHandle element

### F.7.8 Access handle (EXTENDED)

#### F.7.8.1 addAccessHandle

Description: Adds an accessHandle with the given pathSegment to the given element.

— Returns: accesHandleID of type String - Handle to a new accessHandle
— Input: elementID of type String - Handle to an element
— Input: pathSegment of type String - patheSegment value

#### F.7.8.2 addAccessHandleIndex

Description: Adds an index on an accessHandle of type Port.

— Returns: indexID of type String - the index identifier
— Input: accessHandleID of type String - Handle to an accessHandle of type Port
— Input: value of type String - the index value to set on the index

#### F.7.8.3 addAccessHandlePathSegment

Description: Adds a pathSegment with the given pathSegmentName to the given AccessHandle element.

— Returns: pathSegmentID of type String - Handle to a new pathSegment
— Input: accessHandleID of type String - Handle to an accessHandle element
— Input: pathSegment of type String - pathSegment name

#### F.7.8.4 addAccessHandleSlice

Description: Adds a slice with the given pathSegmentValue to the given accessHandle element.

— Returns: sliceID of type String - Handle to the added slice
— Input: accessHandleID of type String - Handle to accessHandle
— Input: pathSegment of type String - Handle to a pathSegment

#### F.7.8.5 addAccessHandleViewRef

Description: Adds a viewRef with the given name to the given accessHandle element.

— Returns: viewRefID of type String - Handle to a viewRef element
— Input: accessHandleID of type String - Handle to an accessHandle element
— Input: viewRef of type String - View reference

#### F.7.8.6 removeAccessHandle

Description: Removes the given accessHandle.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: accessHandleID of type String - Handle to an accessHandle element

#### F.7.8.7 removeAccessHandleIndex

Description: Removes the given index from its containing port accessHandle indices.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indexID of type String - Handle to an index element

#### F.7.8.8 removeAccessHandlePathSegment

Description: Removes the given pathSegment.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: pathSegmentID of type String - Handle to a pathSegment element

#### F.7.8.9 removeAccessHandleSlice

Description: Removes the given slice.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: sliceID of type String - Handle to a slice element

#### F.7.8.10 removeAccessHandleViewRef

Description: Removes the viewRef with the given name from the given accessHandle element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: viewRefID of type String - Handle to a viewxRef element

#### F.7.8.11 setAccessHandleForce

Description: Sets the given value for the attribute force for the given accessHandle element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: accessHandleID of type String - Handle to an accessHandle element
— Input: force of type Boolean - Value of the attribute force

### F.7.9 Access policy (BASE)

#### F.7.9.1 getAccessPolicyAccess

Description: Returns the access defined on the given accessPolicy element.

— Returns: access of type String - The access value
— Input: accessPolicyID of type String - Handle to an accessPolicy element

#### F.7.9.2 getAccessPolicyModeRefByID

Description: Returns the handle to the referenced mode defined on the given accessPolicy element.

— Returns: modeID of type String - Handle to the referenced mode element
— Input: accessPolicyID of type String - Handle to an accessPolicy element
— Input: modeRef of type String - The referenced mode

#### F.7.9.3 getAccessPolicyModeRefByNames

Description: Returns all the modeRef names defined on the accessPolicy element.

— Returns: modeRef of type String - List of the modeRef names
— Input: accessPolicyID of type String - Handle to an accessPolicy element

#### F.7.9.4 getAccessPolicyModeRefIDs

Description: Returns the handles to all the modeRef idefined on the given accessPolicy element.

— Returns: modeRefIDs of type String - List of handles to the modeRef elements
— Input: accessPolicyID of type String - Handle to an accessPolicy element

#### F.7.9.5 getAccessRestrictionModeRefIDs

Description: Returns the handles to all the modeRefs defined on the given accessRestriction element.

— Returns: modeRefIDs of type String - List of handles to the modeRef elements
— Input: accessRestrictionID of type String - Handle to an accessRestriction element

#### F.7.9.6 getAccessRestrictionModeRefbyID

Description: Returns the modeID defined on the given accessRestriction element.

— Returns: modeID of type String - Handle to the referenced mode element
— Input: accessRestrictionID of type String - Handle to an accessRestriction element
— Input: modeRef of type String - Handle to the referenced modeRef element

#### F.7.9.7 getAccessRestrictionModeRefbyNames

Description: Returns all the modeRef defined on the given accessRestriction element.

— Returns: modeRef of type String - The list of all the modeRef values
— Input: accessRestrictionID of type String - Handle to an accessRestriction element

#### F.7.9.8 getAccessRestrictionReadAccessMask

Description: Returns the readAccessMask value defined on the given accessRestriction element.

— Returns: readAccessMask of type Long - The readAccessMask value
— Input: accessRestrictionID of type String - Handle to an accessRestriction element

#### F.7.9.9 getAccessRestrictionReadAccessMaskExpression

Description: Returns the readAccessMask expression defined on the given accessRestriction element.

— Returns: readAccessMask of type String - The readAccessMask expression
— Input: accessRestrictionID of type String - Handle to an accessRestriction element

#### F.7.9.10 getAccessRestrictionReadAccessMaskID

Description: Returns the handle to the readAccessMask defined on the given accessRestriction element.

— Returns: readAccessMaskID of type String - Handle to the readAccessMask element
— Input: accessRestrictionID of type String - Handle to an accessRestriction element

#### F.7.9.11 getAccessRestrictionWriteAccessMask

Description: Returns the writeAccessMask value defined on the given accessRestriction element.

— Returns: writeAccessMask of type Long - The writeAccessMask value
— Input: accessRestrictionID of type String - Handle to an accessRestriction element

#### F.7.9.12 getAccessRestrictionWriteAccessMaskExpression

Description: Returns the writeAccessMask expression on an accessRestriction element.

— Returns: writeAccessMask of type String - The writeAccessMask expression
— Input: accessRestrictionID of type String - Handle to an accessRestriction element

#### F.7.9.13 getAccessRestrictionWriteAccessMaskID

Description: Returns the handle to the readAccessMask element defined on the given accessRestriction
element.

— Returns: writeAccessMaskID of type String - Handle to the writeAccessMask element
— Input: accessRestrictionID of type String - Handle to an accessRestriction element

#### F.7.9.14 getAlternateRegisterAccessPolicyIDs

Description: Returns the handles to all the accessPolicies defined on the given alternateRegister element.

— Returns: accessPolicyID of type String - List of handles to the accessPolicy elements
— Input: alternateRegisterID of type String - Handle to an alternateRegister element

#### F.7.9.15 getBankAccessPoliciesIDs

Description: Returns the handles to all the accessPolicies defined on the given bank element.

— Returns: accessPoliciesIDs of type String - List of handles to the accessPolicies elements
— Input: bankID of type String - Handle to a bank element

#### F.7.9.16 getFieldAccessPoliciesFieldAccessPolicyIDs

Description: Returns the handles to all the fieldAccessPolicies defined on the given fieldAccessPolicies
element

— Returns: fieldAccessPolicyIDs of type String - List of handes to the fieldAccessPolicy elements
— Input: fieldAccessPoliciesID of type String - Handle to a fieldAccessPolicies element

#### F.7.9.17 getFieldAccessPolicyAccess

Description: Returns the access defined on the given fieldAccessPolicy element.

— Returns: access of type String - The access value
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element

#### F.7.9.18 getFieldAccessPolicyAccessRestrictionIDs

Description: Returns the handles to all the accessRestrictions defined on the given fieldAccessPolicy
element.

— Returns: accessRestrictionIDs of type String - List of handles to the accessRestriction elements

— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element

#### F.7.9.19 getFieldAccessPolicyFieldAccessPolicyDefinitionRefByExternalTypeDefID

Description: Returns the handle to the externalTypeDefinitions referenced by the typeDefinitions attribute
of the fieldAccessPolicyDefinitionRef defined on the given fieldAccessPolicy element.

— Returns: fieldAccesspolicyDefinitionRefID of type String - Handle to the externalTypeDefinitions element referenced by the typeDefinitions attribute
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element

#### F.7.9.20 getFieldAccessPolicyFieldAccessPolicyDefinitionRefByID

Description: Returns the handle to the fieldAccesspolicyDefinition referenced from the given

— Returns: fieldAccesspolicyDefinitionRefID of type String - Handle to the referenced fieldAccesspolicyDefinition element
— Input: fieldAccessPolicyID of type String - Handle a fieldAccessPolicy element

#### F.7.9.21 getFieldAccessPolicyFieldAccessPolicyDefinitionRefByName

Description: Returns the fieldAccessPolicyDefinition defined on the given fieldAccessPolicy element.

— Returns: fieldAccesspolicyDefinition of type String - The fieldAccesspolicyDefinition name
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element

#### F.7.9.22 getFieldAccessPolicyFieldAccessPolicyDefinitionRefID

Description: Returns the handle to the fieldAccesspolicyDefinitionRef defined on the given
fieldAccessPolicy element.

— Returns: fieldAccesspolicyDefinitionRefID of type String - Handle to the fieldAccesspolicyDefinitionRef element
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element

#### F.7.9.23 getFieldAccessPolicyModeRefByName

Description: Returns all the modeRefs defined on the given fieldAccessPolicy element.

— Returns: modeRefs of type String - List of the referenced modes
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element

#### F.7.9.24 getFieldAccessPolicyModeRefIDs

Description: Returns the handles to all the modeRefs defined on the given fieldAccessPolicy element.

— Returns: modeRefIDs of type String - List of handles to the modeRef elements
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy

#### F.7.9.25 getFieldAccessPolicyModifiedWriteValue

Description: Returns the modifiedWriteValue defined on the given accessPolicy element.

— Returns: modifiedWriteValue of type String - The value of the modifiedWriteValue element
— Input: accessPolicyID of type String - Handle to an accessPolicy element

#### F.7.9.26 getFieldAccessPolicyModifiedWriteValueID

Description: Returns the handle to the modifiedWriteValue defined on the given fieldAccesspolicy.

— Returns: modifiedWriteValueID of type String - Handle to the modifiedWriteValue element
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element

#### F.7.9.27 getFieldAccessPolicyReadAction

Description: Returns the readAction on a fieldAccessPolicy element.

— Returns: readAction of type String - The readAction value
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element

#### F.7.9.28 getFieldAccessPolicyReadActionID

Description: Returns the handle to the readAction defined on the given fieldAccessPolicy element.

— Returns: readActionID of type String - Handle to the readAction element
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element

#### F.7.9.29 getFieldAccessPolicyReadResponse

Description: Returns the readResponse value defined on the given fieldAccessPolicy element.

— Returns: readResponse of type Long - The readResponse value
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element

#### F.7.9.30 getFieldAccessPolicyReadResponseExpression

Description: Returns the readResponse expression defined on the given fieldAccessPolicy element.

— Returns: readResponse of type String - The readResponse expression value
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element

#### F.7.9.31 getFieldAccessPolicyReadResponseID

Description: Returns the handle to the readResponse element defined on the given fieldAccessPolicy
element.

— Returns: readResponseID of type String - Handle to the readResponse element
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element

#### F.7.9.32 getFieldAccessPolicyReserved

Description: Returns the reserved value on the fieldAccessPolicy element.

— Returns: value of type Boolean - The reserved value on the fieldAccessPolicy element
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element

#### F.7.9.33 getFieldAccessPolicyReservedExpression

Description: Returns the reserved expression on the fieldAccessPolicy element.

— Returns: reserved of type String - The reserved expression on the fieldAccessPolicy element
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element

#### F.7.9.34 getFieldAccessPolicyReservedID

Description: Returns the handle to the reserved element defined on the given fieldAccessPolicy element.

— Returns: reservedID of type String - Handle to the reserved element
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element

#### F.7.9.35 getFieldAccessPolicyTestable

Description: Returns the testable value on the fieldAccessPolicy element.

— Returns: value of type Boolean - The testable value
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element

#### F.7.9.36 getFieldAccessPolicyTestableID

Description: Returns the handle to the testable element defined on the given fieldAccessPolicy element.

— Returns: testableID of type String - Handle to the testable element
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element

#### F.7.9.37 getFieldAccessPolicyWriteValueConstraintID

Description: Returns the handle to the writeValueConstraint defined on the given fieldAccesspolicy.

— Returns: writeValueConstraintID of type String - Handle to the writeValueConstraint element
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element

#### F.7.9.38 getFieldAccesspolicyBroadcastToIDs

Description: Returns the handles to all the broadcastTo elements defined on the given fieldAccessPolicy
element.

— Returns: broadcastToIDs of type String - Handles to the list of broadcastTo elements
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element

#### F.7.9.39 getRegisterAccessPolicyIDs

Description: Returns the handles to all the accessPolicies defined on the given register element.

— Returns: accessPoliciesIDs of type String - List of handles to the accessPolicies elements
— Input: registerID of type String - Handle to a register element

#### F.7.9.40 getRegisterFieldFieldAccessPoliciesID

Description: Returns the handle to the fieldAccessPolicies defined on the given registerField element.

— Returns: fieldAccessPoliciesID of type String - Handle to the fieldAccessPolicies element
— Input: registerFieldID of type String - Handle to a register field element

#### F.7.9.41 getTypeDefinitionsFieldAccessPolicyDefinitionIDs

Description: Returns the handles to all the fieldAccessPolicyDefinitions defined on the given
typeDefinitions element.

— Returns: fieldAccessPolicyDefinitionIDs of type String - List of handles to the fieldAccessPolicyDefinitionID elements
— Input: typeDefinitionsID of type String - Handle to a typeDefinitions element

#### F.7.9.42 getWriteValueConstraintMaximum

Description: Returns the maximum value defined on the given writeValueConstraint element.

— Returns: maximum of type Long - The maximum value
— Input: writeValueConstraintID of type String - Handle to a writeValueConstraint element

#### F.7.9.43 getWriteValueConstraintMaximumExpression

Description: Returns the maximum expression defined on the given writeValueConstraint element.

— Returns: maximum of type String - The maximum expression value
— Input: writeValueConstraintID of type String - Handle to a writeValueConstraint element

#### F.7.9.44 getWriteValueConstraintMaximumID

Description: Returns the handle to the maximum element defined on the given writeValueConstraint
element.

— Returns: maximumID of type String - Handle to the maximum element
— Input: writeValueConstraintID of type String - Handle to a writeValueConstraint element

#### F.7.9.45 getWriteValueConstraintMinimum

Description: Returns the minimum value defined on the given writeValueConstraint element.

— Returns: minimum of type Long - The minimum value
— Input: writeValueConstraintID of type String - Handle to a writeValueConstraint element

#### F.7.9.46 getWriteValueConstraintMinimumExpression

Description: Returns the minimum expression defined on the given writeValueConstraint element.

— Returns: minimum of type String - The minimum expression value
— Input: writeValueConstraintID of type String - Handle to a writeValueConstraint element

#### F.7.9.47 getWriteValueConstraintMinimumID

Description: Returns the handle to the minimum element defined on the given writeValueConstraint
element.

— Returns: minimumID of type String - Handle to the minimum element
— Input: writeValueConstraintID of type String - Handle to a writeValueConstraint element

#### F.7.9.48 getWriteValueConstraintUseEnumeratedValues

Description: Returns the UseEnumeratedValues field on a writeValueConstraint element.

— Returns: value of type Boolean - The UseEnumeratedValues value
— Input: writeValueConstraintID of type String - Handle to a writeValueConstraint element

#### F.7.9.49 getWriteValueConstraintWriteAsRead

Description: Returns the writeAsRead value defined on the given writeValueConstraint element.

— Returns: value of type Boolean - The writeAsRead value
— Input: writeValueConstraintID of type String - Handle to a writeValueConstraint element

### F.7.10 Access policy (EXTENDED)

#### F.7.10.1 addAccessRestrictionModeRef

Description: Adds a modeRef to the given accessRestriction element.

— Returns: modeRefID of type String - the modeRef identifier
— Input: accessRestrictionID of type String - Handle to an accessRestriction element
— Input: modeRef of type String - Name of the referenced mode
— Input: priority of type Long - The mode reference priority

#### F.7.10.2 addAddressBlockAccessPolicy

Description: Adds an accessPolicy element on the addressBlock.

— Returns: accessPolicyID of type String - Handle to the added accessPolicy
— Input: addressBlockID of type String - Handle to an addressblock

#### F.7.10.3 addAlternateRegisterAccessPolicy

Description: Adds accessPolicy for the given alternateRegister.

— Returns: accessPolicyID of type String - Handle to the added accessPolicy
— Input: registerID of type String - Handle to an alternate register

#### F.7.10.4 addExternalTypeDefinitionsResetTypeLink

Description: Adds a resetTypeLink to an externalTypeDefinitions.

— Returns: resetTypeLinkID of type String - The identifier of the added resetTypeLink
— Input: externalTypeDefinitionsID of type String - Handle to an externalTypeDefinitions
— Input: externalResetTypeReference of type String - Handle to the externalResetTypeReference to set on the resetTypeLink
— Input: resetTypeReference of type String - Handle to the resetTypeReference to set on the resetTypeLink

#### F.7.10.5 addFieldAccessPoliciesFieldAccessPolicy

Description: Adds an fieldAccessPolicy on the given fieldAccessPolicies element

— Returns: fieldAccessPolicyID of type String - the fieldAccessPolicy identifier
— Input: fieldAccessPoliciesID of type String - Handle to a fieldAccessPolicies element

#### F.7.10.6 addFieldAccessPolicyAccessRestriction

Description: Adds an accessRestriction to a fieldAccessPolicy element.

— Returns: accessRestrictionID of type String - the accessRestriction identifier
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element

#### F.7.10.7 addFieldAccessPolicyBroadcastTo

Description: Adds a broadcast to the given fieldAccessPolicy element.

— Returns: broadcastToID of type String - Handle of the broadcastTo element
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element
— Input: memoryMapRef of type String - Name of the broadcasted memoryMap
— Input: addressBlockRef of type String - Name of the broadcasted addressBlock
— Input: registerRef of type String - Name of the broadcasted register
— Input: fieldRef of type String - Name of the broadcasted field

#### F.7.10.8 addFieldAccessPolicyModeRef

Description: Adds a modeRef on the given fieldAccessPolicy.

— Returns: modeRefID of type String - Handle to the added modeRef
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element
— Input: modeRef of type String - Name of the referenced mode
— Input: priority of type Long - Priority of the modeRef

#### F.7.10.9 addFieldDefinitionFieldAccessPolicy

Description: Adds an accessPolicy to the given fieldDefinition.

— Returns: fieldAccessPolicyID of type String - Handle to the added AccessEntry
— Input: fieldDefinitionID of type String - Handle to a fieldDefinition element

#### F.7.10.10 addRegisterAccessPolicy

Description: Adds accessPolicy on the given register element.

— Returns: accessPolicyID of type String - Handle to the added accessPolicy
— Input: registerID of type String - Handle to a register element

#### F.7.10.11 addRegisterFileAccessPolicy

Description: Adds an accessPolicy on a registerFile element.

— Returns: accessPolicyID of type String - The accessPolicy identifier
— Input: registerFileID of type String - Handle to a registerFile element

#### F.7.10.12 removeAccessPolicyAccess

Description: Removes the access field on the given accessPolicy.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: accessPolicyID of type String - Handle to an accessPolicy element

#### F.7.10.13 removeAccessRestrictionModeRef

Description: Removes a modeRef from its containing accessRestriction element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: modeRefID of type String - Name of the referenced mode

#### F.7.10.14 removeAccessRestrictionReadAccessMask

Description: Removes a readAccessMask on an accessRestriction element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: accessRestrictionID of type String - Handle to an accessRestriction element

#### F.7.10.15 removeAccessRestrictionWriteAccessMask

Description: Removes a writeAccessMask on an accessRestriction element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: accessRestrictionID of type String - Handle to an accessRestriction element

#### F.7.10.16 removeAddressBlockAccessPolicyID

Description: Removes the given accessPolicy from its containing addressBlock element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: accessPolicyID of type String - Handle to an accessPolicy element

#### F.7.10.17 removeAlternateRegisterAccessPolicy

Description: Removes the given accessPolicy from its containing alternateRegister element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: accessPolicyID of type String - Handle to an accessPolicy

#### F.7.10.18 removeFieldAccessPoliciesFieldAccessPolicy

Description: Removes the given fieldAccessPolicy from its containing fieldAccessPolicies element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldAccessPoliciesID of type String - Handle to an fieldAccessPolicies element

#### F.7.10.19 removeFieldAccessPolicyAccess

Description: Removes the access Attribute on the given fieldAccessPolicy.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element

#### F.7.10.20 removeFieldAccessPolicyAccessRestriction

Description: Removes the given accessRestriction from its containing element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: accessRestrictionID of type String - Handle to an accessRestriction element

#### F.7.10.21 removeFieldAccessPolicyBroadcastTo

Description: Removes the given broadcastTo from its containing fieldAccessPolicy element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: broadcastToID of type String - Handle to a broadcastTo element

#### F.7.10.22 removeFieldAccessPolicyFieldAccessPolicyDefinitionRef

Description: Removes the given fieldAccessPolicyDefinitionRef from its containing fieldAccessPolicy
element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element

#### F.7.10.23 removeFieldAccessPolicyModeRef

Description: Removes the given modeRef from its containing fieldAccessPolicy element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: modeRefID of type String - Handle to a modeRef element

#### F.7.10.24 removeFieldAccessPolicyModifiedWriteValue

Description: Removes the value of the modifiedWriteValue of the given fieldAccessPolicy.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldAccessPolicyID of type String - Handle to the fieldAccessPolicy

#### F.7.10.25 removeFieldAccessPolicyReadAction

Description: Removes the value of the readAction of the given fieldAccessPolicy.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldAccessPolicyID of type String - Handle to the fieldAccessPolicy

#### F.7.10.26 removeFieldAccessPolicyReadResponse

Description: Removes the readResponse field on a fieldAccessPolicy element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldAccessPolicyID of type String - Handle to an fieldAccessPolicy element

#### F.7.10.27 removeFieldAccessPolicyReserved

Description: Removes the Reserved value for fieldAccessPolicy element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element

#### F.7.10.28 removeFieldAccessPolicyTestable

Description: Removes a testable element on the given fieldAccessPolicy.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element

#### F.7.10.29 removeFieldAccessPolicyWriteValueConstraint

Description: Removes the writeValueConstraint elements from the given fieldAccessPolicy element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element

#### F.7.10.30 removeFieldDefinitionFieldAccessPolicy

Description: Removes the given field accessPolicy from its containing FileDefinition element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: accessPolicyID of type String - Handle to an accessPolicy element

#### F.7.10.31 removeRegisterAccessPolicy

Description: Removes the given accessPolicy from its containing register element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: accessPolicyID of type String - Handle to an accessPolicy

#### F.7.10.32 removeRegisterFileAccessPolicy

Description: Removes the given accessPolicy from its containing registerFile element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: accessPolicyID of type String - Handle to an accessPolicy element

#### F.7.10.33 setAccessPolicyAccess

Description: Sets the access field on the given accessPolicy.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: accessPolicyID of type String - Handle to an accessPolicy element
— Input: access of type String - Access enumerated value. Can be one of: read-only, write-only,

read-write, writeOnce, read-writeOnce or no-access

#### F.7.10.34 setAccessRestrictionReadAccessMask

Description: Sets a readAccessMask on an accessRestriction element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: accessRestrictionID of type String - Handle to an accessRestriction element
— Input: readAccessMask of type String - Value of the readAccessMask

#### F.7.10.35 setAccessRestrictionWriteAccessMask

Description: Sets a writeAccessMask on an accessRestriction element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: accessRestrictionID of type String - Handle to an accessRestriction element
— Input: writeAccessMask of type String - Value of the writeAccessMask

#### F.7.10.36 setFieldAccessPolicyAccess

Description: Sets the access Attribute on the given fieldAccessPolicy.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element
— Input: access of type String - Access enumerated value. Can be one of: read-only, write-only, read-write, writeOnce, read-writeOnce or no-access

#### F.7.10.37 setFieldAccessPolicyFieldAccessPolicyDefinitionRef

Description: Sets the FieldAccessPolicyDefinitionRef on the given fieldAccesspolicy.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element
— Input: value of type String - Name of the referenced fieldAccessPolicyDefinition in an external typeDefinitions
— Input: typeDefinitions of type String - Name of the component externalTypeDefinitions

#### F.7.10.38 setFieldAccessPolicyModifiedWriteValue

Description: Sets the value of the modifiedWriteValue of the given fieldAccessPolicy.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldAccessPolicyID of type String - Handle to the fieldAccessPolicy
— Input: value of type String - Value of the modifiedWriteValue. Can be one of: oneToClear, one-

ToSet, oneToToggle, zeroToClear, zeroToSet, zeroToToggle, clear, set or modify.

#### F.7.10.39 setFieldAccessPolicyReadAction

Description: Sets the read action field on a fieldAccessPolicy element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldAccessPolicyID of type String - Handle to an fieldAccessPolicy element
— Input: readAction of type String - the readAction value to set

#### F.7.10.40 setFieldAccessPolicyReadResponse

Description: Sets the readResponse field on a fieldAccessPolicy element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldAccessPolicyID of type String - Handle to an fieldAccessPolicy element
— Input: readResponse of type String - The readResponse value to set

#### F.7.10.41 setFieldAccessPolicyReserved

Description: Sets the Reserved value for fieldAccesspolicy element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element
— Input: reserved of type String - Reserved value

#### F.7.10.42 setFieldAccessPolicyTestable

Description: Sets a testable element on the given fieldAccesspolicy.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element
— Input: testable of type Boolean - Handle to value of the added testable

#### F.7.10.43 setFieldAccessPolicyWriteValueConstraintMinMax

Description: Sets a writeValueConstraint with a minimum and maximum on fieldAccessPolicy with all his
mandatory attribute.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element
— Input: minimum of type String - The minimum value
— Input: maximum of type String - The maximum value

#### F.7.10.44 setFieldAccessPolicyWriteValueConstraintUseEnumeratedValue

Description: Sets a writeValueConstraint with a useEnumeratedValue on fieldAccessPolicy with all his
mandatory attribute.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element
— Input: useEnumeratedValue of type Boolean - The useEnumeratedValue value

#### F.7.10.45 setFieldAccessPolicyWriteValueConstraintWriteAsRead

Description: Sets a writeValueConstraint with a writeAsRead on fieldAccessPolicy with all his mandatory
attribute.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldAccessPolicyID of type String - Handle to a fieldAccessPolicy element
— Input: writeAsRead of type Boolean - The writeAsRead value

#### F.7.10.46 setWriteValueConstraintMaximum

Description: Sets the maximum field on a writeValueConstraint element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: writeValueConstraintID of type String - Handle to a writeValueConstraint element
— Input: maximum of type String - Maximum value

#### F.7.10.47 setWriteValueConstraintMinimum

Description: Sets the minimum on a writeValueConstraint element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: writeValueConstraintID of type String - Handle to a writeValueConstraint element
— Input: minimum of type String - Minimum value

#### F.7.10.48 setWriteValueConstraintUseEnumeratedValues

Description: Sets the UseEnumeratedValues on a writeValueConstraint element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: writeValueConstraintID of type String - Handle to a writeValueConstraint element
— Input: useEnumeratedValues of type Boolean - True to only allow write enumeration values to be written

#### F.7.10.49 setWriteValueConstraintWriteAsRead

Description: Sets the writeAsRead element of the given writeValueConstraint element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: writeValueConstraintID of type String - Handle to a writeValueConstraint element
— Input: writeAsRead of type Boolean - True if the access is writeAsRead

### F.7.11 Address space (BASE)

#### F.7.11.1 getAddressSpaceAddressUnitBits

Description: Returns the addressUnitBits defined on the given addressSpace element.

— Returns: addressUnitBits of type Long - The addressUnitBits value
— Input: addressSpaceID of type String - Handle to an addressSpace element

#### F.7.11.2 getAddressSpaceAddressUnitBitsExpression

Description: Returns the addressUnitBits expression on the given address space element.

— Returns: addressUnitBitsExpression of type String - The addressUnitBits expression
— Input: addressSpaceID of type String - Handle to an addressSpace element

#### F.7.11.3 getAddressSpaceAddressUnitBitsID

Description: Returns the handle to the addressUnitBits defined on the given addressSpace element.

— Returns: addressUnitBitsID of type String - Handle to the addressUnitBits
— Input: addressSpaceID of type String - Handle to an addressSpace element

#### F.7.11.4 getAddressSpaceLocalMemoryMapID

Description: Returns the handle to the localMemoryMap defined on the given addressSpace element.

— Returns: localMemoryMapID of type String - Handle to a localMemoryMap element
— Input: addressSpaceID of type String - Handle to an addressSpace element

#### F.7.11.5 getAddressSpaceRange

Description: Returns the range defined on the given addressSpace element.

— Returns: range of type Long - The range value
— Input: addressSpaceID of type String - Handle to an addressSpace element

#### F.7.11.6 getAddressSpaceRangeExpression

Description: Returns the range expression defined on the given addressSpace element.

— Returns: rangeExpression of type String - The addressSpace range
— Input: addressSpaceID of type String - Handle to an addressSpace element

#### F.7.11.7 getAddressSpaceRangeID

Description: Returns the handle to the range defined on the given addressSpace element.

— Returns: rangeID of type String - Handle to the range
— Input: addressSpaceID of type String - Handle to an addressSpace element

#### F.7.11.8 getAddressSpaceSegmentIDs

Description: Returns the handles to all the segments defined on the given addressSpace element.

— Returns: segmentIDs of type String - List of handles to the segment elements
— Input: addressSpaceID of type String - Handle to an addressSpace element

#### F.7.11.9 getAddressSpaceWidth

Description: Returns the width defined on the given addressSpace element.

— Returns: width of type Long - The width value
— Input: addressSpaceID of type String - Handle to an addressSpace element

#### F.7.11.10 getAddressSpaceWidthExpression

Description: Returns the width expression defined on the given addressSpace element.

— Returns: widthExpression of type String - The addressSpace width
— Input: addressSpaceID of type String - Handle to an addressSpace element

#### F.7.11.11 getAddressSpaceWidthID

Description: Returns the handle to the width defined on the given addressSpace element.

— Returns: widthID of type String - Handle to the width
— Input: addressSpaceID of type String - Handle to an addressSpace element

#### F.7.11.12 getAliasOfAddressSpaceRefByName

Description: Returns the addressSpaceRef defined on the given aliasOf element.

— Returns: addressSpaceRef of type String - The referenced addressSpace
— Input: aliasOfID of type String - Handle to an aliasOf element

#### F.7.11.13 getAliasOfAddressSpaceRefID

Description: Returns the handle to the addressSpaceRef defined on the given aliasOf element.

— Returns: addressSpaceRefID of type String - Handle to the addressSpaceRef element
— Input: aliasOfID of type String - Handle to an aliasOf element

#### F.7.11.14 getLocalMemoryMapAddressBlockIDs

Description: Returns the handles to all the localAddressBlocks defined on the given addressSpace element.

— Returns: localAddressBlockIDs of type String - Handle to a localAddressBlock element
— Input: addressSpaceID of type String - Handle to an addressSpace element

#### F.7.11.15 getLocalMemoryMapBankIDs

Description: Returns the handles to all the localBanks defined on the given addressSpace element.

— Returns: localBankIDs of type String - List of handles to localBank elements
— Input: addressSpaceID of type String - Handle to an addressSpace element

#### F.7.11.16 getRegionAddressOffset

Description: Returns the addressOffset on a region element.

— Returns: addressOffset of type Long - The addressOffset value
— Input: regionID of type String - Handle to a region element

#### F.7.11.17 getRegionAddressOffsetExpression

Description: Returns the addressOffset expression on a region element.

— Returns: addressOffset of type String - The addressOffset expression
— Input: regionID of type String - Handle to a region element

#### F.7.11.18 getRegionAddressOffsetID

Description: Returns the handle to the addressOffset defined on the given region element.

— Returns: addressOffsetID of type String - Handle to the addressOffset element
— Input: regionID of type String - Handle to a region element

#### F.7.11.19 getRegionRange

Description: Returns the range defined on the given region element.

— Returns: rangeValue of type Long - The range value
— Input: regionID of type String - Handle to a region element

#### F.7.11.20 getRegionRangeExpression

Description: Returns the range expression defined on the given region element.

— Returns: range of type String - The range expression
— Input: regionID of type String - Handle to a region element

#### F.7.11.21 getRegionRangeID

Description: Returns the handle to the range defined on the given region element.

— Returns: rangeID of type String - Handle to the range element
— Input: regionID of type String - Handle to a region element

#### F.7.11.22 getSegmentAddressOffset

Description: Returns the addressOffset defined on the given segment element.

— Returns: addressOffset of type Long - The address offset
— Input: segmentID of type String - Handle to a segment element

#### F.7.11.23 getSegmentAddressOffsetExpression

Description: Returns the addressOffset expression defined on the given segment element.

— Returns: addressOffset of type String - The addressOffset expression
— Input: segmentID of type String - Handle to a segment element

#### F.7.11.24 getSegmentAddressOffsetID

Description: Returns the handle to the addressOffset defined on the given segment element.

— Returns: addressOffsetID of type String - Handle to the addressOffset
— Input: segmentID of type String - Handle to a segment element

#### F.7.11.25 getSegmentRange

Description: Returns the range defined on the given segment element.

— Returns: range of type Long - The range value
— Input: segmentID of type String - Handle to a segment element

#### F.7.11.26 getSegmentRangeExpression

Description: Returns the range expression defined on the given segment element.

— Returns: range of type String - The range expression
— Input: segmentID of type String - Handle to a segment element

#### F.7.11.27 getSegmentRangeID

Description: Returns the handle to the range defined on the given segment element.

— Returns: rangeID of type String - Handle to the range
— Input: segmentID of type String - Handle to a segment element

### F.7.12 Address space (EXTENDED)

#### F.7.12.1 addAddressSpaceSegment

Description: Adds a segment with the given name, addressOffset, and range to the given addressSpace
element.

— Returns: segmentID of type String - Handle to a new segment element
— Input: addressSpaceID of type String - Handle to an addressSpace element
— Input: name of type String - Segment name
— Input: addressOffset of type String - Segment addressOffset
— Input: range of type String - Segment range

#### F.7.12.2 addExecutableImageFileSetRef

Description: Adds a fileSetRef with the given localName to the given executableImage element.

— Returns: fileSetRefID of type String - Handle to a new fileSetRef
— Input: executableImageID of type String - Handle to an executableImage element
— Input: localName of type String - fileSetRef localName

#### F.7.12.3 addLocalMemoryMapAddressBlock

Description: Adds an addressBlock with the given name, baseAddress, range, and width to the given
localMemoryMap element.

— Returns: addressBlockID of type String - Handle to a new addressBlock element
— Input: localMemoryMapID of type String - Handle to a localMemoryMap element
— Input: name of type String - AddressBlock name
— Input: baseAddress of type String - AddressBlock baseAddress
— Input: range of type String - AddressBlock range
— Input: width of type String - AddressBlock width

#### F.7.12.4 removeAddressSpaceAddressUnitBits

Description: Removes the addressUnitBits on the given address space element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressSpaceID of type String - Handle to an addressSpace element

#### F.7.12.5 removeAddressSpaceLocalMemoryMap

Description: Removes the localMemoryMap on the given addressSpace element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressSpaceID of type String - Handle to an addressSpace element

#### F.7.12.6 removeAddressSpaceSegment

Description: Removes the given segment element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: segmentID of type String - Handle to a segment element

#### F.7.12.7 removeExecutableImageFileSetRef

Description: Removes the fileSetRef with the given fileSetRefID.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileSetRefID of type String - Handle to an fileSetRef element

#### F.7.12.8 removeLinkerCommandFileGenerator

Description: Removes the given generator element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: generatorID of type String - Handle to a generator element

#### F.7.12.9 removeLocalMemoryMapAddressBlock

Description: Removes the given addressBlock element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressBlockID of type String - Handle to an addressBlock element

#### F.7.12.10 removeLocalMemoryMapBank

Description: Removes the given localBank element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: bankID of type String - Handle to a localBank element

#### F.7.12.11 setAddressSpaceAddressUnitBits

Description: Sets the addressUnitBits with the given value to the given address space element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressSpaceID of type String - Handle to an addressSpace element
— Input: addressUnitBitsExpression of type String - AddressSpace addressUnitBits

#### F.7.12.12 setAddressSpaceLocalMemoryMap

Description: Adds a localMemoryMap with the given name to the given addressSpace element with a
default addressBlock and addressBlockDefinitionRef.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressSpaceID of type String - Handle to an addressSpace element
— Input: name of type String - addressSpace name
— Input: addressBlockName of type String - addressBlock name
— Input: baseAddress of type String - baseAddress expression for the addressBlock
— Input: range of type String - addressBlock range
— Input: width of type String - addressBlock width

#### F.7.12.13 setAddressSpaceRange

Description: Sets the range expression of the addressSpace.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressSpaceID of type String - Handle to an addressSpace element
— Input: value of type String - The value of the range expression

#### F.7.12.14 setAddressSpaceWidth

Description: Sets the width expression of the addressSpace.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressSpaceID of type String - Handle to an addressSpace element
— Input: value of type String - Width value expression

#### F.7.12.15 setSegmentAddressOffset

Description: Sets the address offset of the segment.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: segmentID of type String - Handle to a segment element
— Input: value of type String - Value of the address offset

#### F.7.12.16 setSegmentRange

Description: Sets the range expression of the segment.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: segmentID of type String - Handle to a segment element
— Input: value of type String - Value of the range

### F.7.13 Array (BASE)

#### F.7.13.1 getArrayDimIDs

Description: Returns the handles to all the dim elements defined on the given register or registerField array
element.

— Returns: dimID of type String - List of handles to the dim elements
— Input: arrayOrfieldArrayID of type String - Handle to an array element

#### F.7.13.2 getArrayIDs

Description: Returns arraryIDs of the given element.

— Returns: arrayIDs of type String - List of array handles
— Input: arrayContainerElementID of type String - Handle to an element that has an array ele-

ment

#### F.7.13.3 getArrayLeftID

Description: Returns the handle to the left range defined on the given array element.

— Returns: leftID of type String - Handle to the left range
— Input: arrayID of type String - Handle to an array element

#### F.7.13.4 getArrayRange

Description: Returns the range defined on the given array element.

— Returns: range of type Long - Array of two range values: left and right
— Input: arrayID of type String - Handle to an array element

#### F.7.13.5 getArrayRangeExpression

Description: Returns the range expressions defined on the given array element.

— Returns: rangeExpression of type String - Array of two range expressions: left and right
— Input: arrayID of type String - Handle to an array element

#### F.7.13.6 getArrayRightID

Description: Returns the handle to the right range defined on the given array element.

— Returns: rightID of type String - Handle to the right range
— Input: arrayID of type String - Handle to an array element

#### F.7.13.7 getArrayStride

Description: Returns the stride value defined on the given array element.

— Returns: strideValue of type Long - The stride value
— Input: arrayID of type String - Handle to an array element

#### F.7.13.8 getArrayStrideExpression

Description: Returns the stride expression defined on the given array element.

— Returns: strideExpression of type String - The stride expression
— Input: arrayID of type String - Handle to an array element

#### F.7.13.9 getArrayStrideID

Description: Returns the handle to the stride defined on the given register or registerField array element.

— Returns: stride of type String - List of handles to the stride or bitStride elements
— Input: arrayOrfieldArrayID of type String - Handle to an array element

#### F.7.13.10 getDimExpression

Description: Returns the dim expression defined on the given dim element.

— Returns: dim of type String - The dim expression value
— Input: dimID of type String - Handle to a dim element

#### F.7.13.11 getDimIndexVar

Description: Returns the name of the indexVar attribute defined on the given Dim element.

— Returns: indexVar of type String - The index variable
— Input: dimID of type String - Handle to a Dim element

#### F.7.13.12 getDimValue

Description: Returns the dim value defined on the given dim element.

— Returns: dim of type Long - The dim value
— Input: dimID of type String - Handle to a dim element

#### F.7.13.13 getRegisterArrayID

Description: Returns the handle to the array defined on the given register.

— Returns: arrayID of type String - Handle to the register array element
— Input: registerID of type String - Handle to a register element

#### F.7.13.14 getRegisterFieldArrayID

Description: Returns the handle to the array defined on the given register field.

— Returns: arrayID of type String - Handle to the field array element
— Input: registerFieldID of type String - Handle to a register field element

### F.7.14 Array (EXTENDED)

#### F.7.14.1 addArray

Description: Adds an array to the given element.

— Returns: arraryID of type String - Handle to new array
— Input: arrayContainerElementID of type String - Handle to an element that has an array element
— Input: range of type String[] - Range expression with left in index 0 and right in index 1

#### F.7.14.2 addArrayDim

Description: Adds a dim element to an array on a register or a registerField

— Returns: dimID of type String - Handle to the added dim
— Input: arrayOrfieldArrayID of type String - Handle to an array on a register or a register-

Field

— Input: value of type String - the value of the dim element

#### F.7.14.3 removeArray

Description: Removes the given array.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: arraryID of type String - Handle to an array element

#### F.7.14.4 removeArrayDim

Description: Removes the given dimension from its containing array element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: dimID of type String - Handle to a dim element

#### F.7.14.5 removeArrayStride

Description: Removes the stride from the given array element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: arrayID of type String - Handle to an array element

#### F.7.14.6 removeIndexVarAttribute

Description: Removes the indexVar attribute of the given dim element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: dimID of type String - Handle to a dim element

#### F.7.14.7 setArrayStride

Description: Sets the stride value from to the given array element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: arrayID of type String - Handle to an array element
— Input: stride of type String - The stride value to set

#### F.7.14.8 setDimIndexVar

Description: Sets the indexVar attribute of the given Dim element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: dimID of type String - Handle to a Dim element
— Input: value of type String - New value expression

### F.7.15 Assertion (BASE)

#### F.7.15.1 getAssertionAssert

Description: Returns the value of the given assertion element.

— Returns: value of type Boolean - The assertion value
— Input: assertionID of type String - Handle to an assertion element

#### F.7.15.2 getAssertionAssertExpression

Description: Returns the expression of the given assertion element.

— Returns: expression of type String - The assertion expression
— Input: assertionID of type String - Handle to an assertion element

#### F.7.15.3 getAssertionAssertID

Description: Returns the handle to the assert defined on the given assertion element.

— Returns: assertID of type String - Handle to the assert element
— Input: assertionID of type String - Handle to an assertion element

#### F.7.15.4 getAssertionIDs

Description: Returns the handles to all the assertions defined on the given element.

— Returns: assertionIDs of type String - List of handles to assertion elements
— Input: assertionContainerElementID of type String - Handle to an element that has asser-

tion elements

### F.7.16 Assertion (EXTENDED)

#### F.7.16.1 addAssertion

Description: Adds an assertion with the given name and given value to the given element.

— Returns: assertionID of type String - Handle to a new assertion
— Input: assertionContainerElementID of type String - Handle to an element that has asser-

tion elements

— Input: name of type String - Assertion name
— Input: expression of type String - Assertion expression

#### F.7.16.2 removeAssertion

Description: Removes the given assertion.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: assertionID of type String - Handle to an assertion element

#### F.7.16.3 setAssertionAssert

Description: Sets the assert of the given assertion.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: assertionID of type String - Handle to an assertion element
— Input: assertExpression of type String - Assert expression

### F.7.17 Bus definition (BASE)

#### F.7.17.1 getBusDefinitionBroadcast

Description: Returns the broadcast element defined on the given busDef or busDefInstance element.

— Returns: value of type Boolean - The bus broadcast value
— Input: busDefOrBusDefInstanceID of type String - Handle to a busDef or busDefInstance element

#### F.7.17.2 getBusDefinitionChoiceIDs

Description: Returns the handles to all the choices defined on the given bus definition object element.

— Returns: choiceIDs of type String - List of handles to choice elements
— Input: busDefinitionID of type String - Handle to an bus definition object element

#### F.7.17.3 getBusDefinitionDirectConnection

Description: Returns the directConnection element defined on the given busDef or busDefInstance element.

— Returns: value of type Boolean - The bus directionConnection value
— Input: busDefOrBusDefInstanceID of type String - Handle to a busDef or busDefInstance element

#### F.7.17.4 getBusDefinitionExtendsRefByVLNV

Description: Returns the extended VLNV defined on the given busDefinition object.

— Returns: VLNV of type String - The VLNV of the extended busDefinition object
— Input: busDefinitionID of type String - Handle to a busDefinition object

#### F.7.17.5 getBusDefinitionIsAddressable

Description: Returns the isAddressable element defined on the given busDef or busDefInstance element.

— Returns: value of type Boolean - The bus isAddressable value
— Input: busDefOrBusDefInstanceID of type String - Handle to a busDef or busDefInstance element

#### F.7.17.6 getBusDefinitionMaxInitiators

Description: Returns the maxInitiators defined on the given busDef or busDefInstance element.

— Returns: value of type Long - The maximum number of initiators
— Input: busDefOrBusDefInstanceID of type String - Handle to a busDef or busDefInstance element

#### F.7.17.7 getBusDefinitionMaxInitiatorsExpression

Description: Returns the maxInitiators expression defined on the given busDef or busDefInstance element.

— Returns: value of type String - The maxInitiators expression
— Input: busDefOrBusDefInstanceID of type String - Handle to a busDef or busDefInstance element

#### F.7.17.8 getBusDefinitionMaxInitiatorsID

Description: Returns the maximum number of initiators defined on the given busDefinition element.

— Returns: value of type String - The maximum number of initiators that can connect on this bus
— Input: busDefID of type String - Handle to a busDef element

#### F.7.17.9 getBusDefinitionMaxTargets

Description: Returns the maxTargets defined on the given busDef or busDefInstance element.

— Returns: value of type Long - The maximum number of targets
— Input: busDefOrBusDefInstanceID of type String - Handle to a busDef or busDefInstance element

#### F.7.17.10 getBusDefinitionMaxTargetsExpression

Description: Returns the maxTargets expression defined on the given busDefinition element.

— Returns: value of type String - The maxTargets expression
— Input: busDefinitionID of type String - Handle to a busDefinition element

#### F.7.17.11 getBusDefinitionMaxTargetsID

Description: Returns the maximum number of targets defined on the given busDefinition element.

— Returns: value of type String - The maximum number of targets that can connect on this bus
— Input: busDefID of type String - Handle to a busDef element

#### F.7.17.12 getBusDefinitionSystemGroupNameIDs

Description: Returns the handles to all the systemGroupNames defined on the given busDefinition element.

— Returns: systemGroupNameIDs of type String - List of handles to the systemGroupName ele-

ments

— Input: busDefinitionID of type String - Handle to a busDefinition element

### F.7.18 Bus definition (EXTENDED)

#### F.7.18.1 addBusDefinitionChoice

Description: Adds a choice with the given name and enumerations to the given bus definition element.

— Returns: choiceID of type String - Handle to a new choice
— Input: busDefinitionID of type String - Handle to a bus definition element
— Input: name of type String - Choice name
— Input: enumerations of type String[] - List of enumeration values

#### F.7.18.2 addBusDefinitionSystemGroupName

Description: Adds the given system group name to the list of busDefinition systemGroupNames element.

— Returns: systemGroupNameID of type String - The systemGroupName identifier
— Input: busDefinitionID of type String - Handle of a busDefinition element
— Input: value of type String - The systemGroupName value

#### F.7.18.3 removeBusDefinitionBroadcast

Description: Removes broadcast from the given busDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: busDefID of type String - Handle to a busDef element

#### F.7.18.4 removeBusDefinitionChoice

Description: Removes the given choice element from the given busDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: choiceID of type String - Handle to a choice element

#### F.7.18.5 removeBusDefinitionExtends

Description: Removes extends from the given busDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: busDefID of type String - Handle to a busDef element

#### F.7.18.6 removeBusDefinitionMaxInitiators

Description: Removes maxInitiators for the given busDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: busDefID of type String - Handle to a busDef element

#### F.7.18.7 removeBusDefinitionMaxTargets

Description: Removes maxTargets for the given busDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: busDefID of type String - Handle to a busDef element

#### F.7.18.8 setBusDefinitionBroadcast

Description: Sets broadcast with the given value for the given busDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: busDefID of type String - Handle to a busDef element
— Input: value of type Boolean - BusDef broadcast

#### F.7.18.9 setBusDefinitionDirectConnection

Description: Sets directionConnection with the given value for the given busDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: busDefID of type String - Handle to a busDef element
— Input: value of type Boolean - BusDef directionConnection

#### F.7.18.10 setBusDefinitionExtends

Description: Sets extends with the given value for the given busDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: busDefID of type String - Handle to a busDef element

— Input: busDefVLNV of type String[] - BusDef VLNV

#### F.7.18.11 setBusDefinitionIsAddressable

Description: Sets isAddressable with the given value for the given busDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: busDefID of type String - Handle to a busDef element
— Input: value of type Boolean - BusDef isAddressable

#### F.7.18.12 setBusDefinitionMaxInitiators

Description: Sets maxInitiators with the given value for the given busDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: busDefID of type String - Handle to a busDef element
— Input: valueExpression of type String - BusDef maxInitiators

#### F.7.18.13 setBusDefinitionMaxTargets

Description: Sets maxTargets with the given value for the given busDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: busDefID of type String - Handle to a busDef element
— Input: valueExpression of type String - BusDef maxTargets

### F.7.19 Bus interface (BASE)

#### F.7.19.1 getAbstractionTypeAbstractionRefByID

Description: Returns the handle to the abstractionDefinition instance referenced from the given
abtractionType element

— Returns: abstractionDefinitionID of type String - Handle to the referenced abstraction-

Definition object

— Input: abstractionTypeID of type String - Handle to an abstractionType element

#### F.7.19.2 getAbstractionTypeAbstractionRefByVLNV

Description: Returns the VLNV of the abstractionDefinition referenced from the given abtractionType
element.

— Returns: VLNV of type String - The VLNV of the referenced abstractionDefinition object
— Input: abstractionTypeID of type String - Handle to an abstractionType element

#### F.7.19.3 getAbstractionTypePortMapIDs

Description: Returns the handles to all the portMaps defined on the given abstractionType element.

— Returns: portMapIDs of type String - List of handles to the portMap elements
— Input: abstractionTypeID of type String - Handle to an abstractionType element

#### F.7.19.4 getAbstractionTypeViewRefByID

Description: Returns all the viewRefs defined on the given abstractionType element.

— Returns: viewID of type String - Handle to the referenced view
— Input: abstractionTypeID of type String - Handle to an abstractionType element
— Input: viewRef of type String - Handle to the viewRef element

#### F.7.19.5 getAbstractionTypeViewRefByNames

Description: Returns all the viewRefs defined on the given abstractionType element.

— Returns: viewRefs of type String - List of the referenced views
— Input: abstractionTypeID of type String - Handle to an abstractionType element

#### F.7.19.6 getAbstractionTypeViewRefIDs

Description: Returns the handles to all the viewRefs defined on the given abstractionType element.

— Returns: viewRefsIDs of type String - List of handles to the viewRef elements
— Input: abstractionTypeID of type String - Handle to an abstractionType element

#### F.7.19.7 getAddressSpaceRefBaseAddress

Description: Returns the baseAddress resolved value on an addressSpaceRef element

— Returns: baseAddressValue of type Long - The resolved baseAddress value
— Input: addressSpaceRefID of type String - Handle to an addressSpaceRef element

#### F.7.19.8 getAddressSpaceRefBaseAddressExpression

Description: Returns the baseAddress expression on an addressSpaceRef element

— Returns: baseAddressExpression of type String - The baseAddress expression
— Input: addressSpaceRefID of type String - Handle to an addressSpaceRef element

#### F.7.19.9 getAddressSpaceRefBaseAddressID

Description: Returns the handle to the baseAddress defined on the given addressSpaceRef element.

— Returns: baseAddressID of type String - Handle to the baseAddress element
— Input: addressSpaceRefID of type String - Handle to an addressSpaceRef element

#### F.7.19.10 getAddressSpaceRefModeRefByID

Description: Returns the handle to the mode referenced from the given addressSpaceRef element.

— Returns: modeID of type String - Handle to the referenced mode element
— Input: addressSpaceRefID of type String - Handle to an addressSpaceRef element
— Input: modeRef of type String - The referenced mode

#### F.7.19.11 getAddressSpaceRefModeRefByNames

Description: Returns all the modeRefs defined on the given addressSpaceRef element

— Returns: modeRefs of type String - List of the referenced modes
— Input: addressSpaceRefID of type String - Handle to an addressSpaceRef element

#### F.7.19.12 getBaseAddressesRange

Description: Returns the range value defined on the given baseAddresses element.

— Returns: rangeValue of type Long - The range value
— Input: baseAddressesID of type String - Handle to a baseAddressses element

#### F.7.19.13 getBaseAddressesRangeExpression

Description: Returns the range expression defined on the given baseAddresses element

— Returns: rangeExpression of type String - The range expression
— Input: baseAddressesID of type String - Handle to a baseAddressses element

#### F.7.19.14 getBaseAddressesRangeID

Description: Returns the handle to the range defined on the given baseAddresses element

— Returns: rangeID of type String - Handle to the range element
— Input: baseAddressesID of type String - Handle to a baseAddressses element

#### F.7.19.15 getBaseAddressesRemapAddressIDs

Description: Returns the handles to all the remapAddress defined on the given baseAddresses element

— Returns: remapAddressesIDs of type String - List of handles to the baseAddress elements
— Input: baseAddressesID of type String - Handle to a baseAddressses element

#### F.7.19.16 getBusInterfaceAbstractionTypeIDs

Description: Returns the handles to all the abstractionTypes defined on the given busInterface element.

— Returns: abstractionTypeIDs of type String - List of handles to the abstractionType elements
— Input: busInterfaceID of type String - Handle to a busInterface element

#### F.7.19.17 getBusInterfaceBitSteering

Description: Returns the bitSteering defined on the given busInterface element.

— Returns: value of type Boolean - The bitSteering value
— Input: busInterfaceID of type String - Handle to a busInterface element

#### F.7.19.18 getBusInterfaceBitSteeringExpression

Description: Returns the bitSteering expression defined on the given busInterface element.

— Returns: valueExpression of type String - The bitSteering expression
— Input: busInterfaceID of type String - Handle to a busInterface element

#### F.7.19.19 getBusInterfaceBitSteeringID

Description: Returns the handle to the bitSteering defined on the given busInterface element.

— Returns: bitSteeringID of type String - Handle to the bitSteering element
— Input: busInterfaceID of type String - Handle to a busInterface element


#### F.7.19.20 getBusInterfaceBitsInLau

Description: Returns the bitsInLau resolved value on a busInterface element.

— Returns: value of type Long - The bitsInLau resolved value
— Input: busInterfaceID of type String - Handle to a busInterface element

#### F.7.19.21 getBusInterfaceBitsInLauExpression

Description: Returns the bitsInLau expression defined on the given busInterface element.

— Returns: bitsInLauExpression of type String - The bitsInLau expression
— Input: busInterfaceID of type String - Handle to a busInterface element

#### F.7.19.22 getBusInterfaceBitsInLauID

Description: Returns the handle to the bitsInLau defined on the given busInterface element.

— Returns: bitsInLauID of type String - Handle to the bitsInLau element
— Input: busInterfaceID of type String - Handle to a busInterface element

#### F.7.19.23 getBusInterfaceBusTypeID

Description: Returns the handle to the busType defined on the given busInterface element.

— Returns: busTypeID of type String - Handle to the busType element
— Input: busInterfaceID of type String - Handle to a busInterface element

#### F.7.19.24 getBusInterfaceBusTypeRefByID

Description: Returns the handle to the busDefinition referenced from the busType defined on the given
busInterface element.

— Returns: busDefinitionID of type String - Handle to the referenced busDefinition object
— Input: busInterfaceID of type String - Handle to a busInterface element

#### F.7.19.25 getBusInterfaceBusTypeRefByVLNV

Description: Returns the VLNV of the busType defined on the given busInterface element.

— Returns: busTypeVLNV of type String - The VLNV of the bus
— Input: busInterfaceID of type String - Handle to a busInterface element

#### F.7.19.26 getBusInterfaceConnectionRequired

Description: Returns the connectionRequired defined on the given busInterface element.

— Returns: value of type Boolean - The connectionRequired value
— Input: busInterfaceID of type String - Handle to a busInterface element

#### F.7.19.27 getBusInterfaceEndianness

Description: Returns the endianness defined on the given busInterface element.

— Returns: value of type String - The endianness value
— Input: busInterfaceID of type String - Handle to a busInterface element

#### F.7.19.28 getBusInterfaceInitiatorID

Description: Returns the handle to the initiator defined on the given busInterface element.

— Returns: initiatorID of type String - Handle to an initiator element
— Input: busInterfaceID of type String - Handle to a busInterface element

#### F.7.19.29 getBusInterfaceInterfaceMode

Description: Returns the interfaceMode defined on the given busInterface element.

— Returns: interfaceMode of type String - The interface mode (initiator, target, system)
— Input: busInterfaceID of type String - Handle to a busInterface element

#### F.7.19.30 getBusInterfaceMirroredSystemID

Description: Returns the handle to the mirroredSystem element defined on the given busInterface element.

— Returns: mirroredSystemID of type String - Handle to the mirroredSystem element
— Input: busInterfaceID of type String - Handle to a busInterface element

#### F.7.19.31 getBusInterfaceMirroredTargetID

Description: Returns the handle to the mirroredTarget element defined on the given busInterface element.

— Returns: mirroredTargetID of type String - Handle to the mirroredTarget element
— Input: busInterfaceID of type String - Handle to a busInterface element

#### F.7.19.32 getBusInterfaceMonitorID

Description: Returns the handle to the monitor element defined on the given busInterface element.

— Returns: monitorID of type String - Handle to the monitor element
— Input: busInterfaceID of type String - Handle to a busInterface element

#### F.7.19.33 getBusInterfaceRefLocalName

Description: Returns the localName defined on the given busInterfaceRef element.

— Returns: localName of type String - The local name
— Input: busInterfaceRefID of type String - Handle to a busInterfaceRef element

#### F.7.19.34 getBusInterfaceSystemID

Description: Returns the handle to the system element defined on the given busInterface element.

— Returns: systemID of type String - Handle to the system element
— Input: busInterfaceID of type String - Handle to a busInterface element

#### F.7.19.35 getBusInterfaceTargetID

Description: Returns the handle to the target defined on the given busInterface element.

— Returns: targetID of type String - Handle to the target element
— Input: busInterfaceID of type String - Handle to a busInterface element

#### F.7.19.36 getChannelBusInterfaceRefByID

Description: Returns the busInterface referenced from the given busInterfaceRef element.

— Returns: busInterfaceID of type String - Handle to the referenced busInterface element
— Input: busInterfaceRefID of type String - Handle to an busInterfaceRef element

#### F.7.19.37 getChannelBusInterfaceRefIDs

Description: Returns the handles to all the busInterfaceRefs defined on the given channel element.

— Returns: busInterfaceRefIDs of type String - List of handles to the busInterfaceRef elements
— Input: channelID of type String - Handle to a channel element

#### F.7.19.38 getFileSetRefGroupGroup

Description: Returns the group defined on the given fileSetRefGroup element.

— Returns: group of type String - The group name
— Input: fileSetRefGroupID of type String - Handle to a fileSetRefGroup element

#### F.7.19.39 getIndirectInterfaceBitsInLauID

Description: Returns the handle to the bitsInLau defined on the given indirectInterface element.

— Returns: bitsInLauID of type String - Handle to the bitsInLau element
— Input: indirectInterfaceID of type String - Handle to an indirectInterface element

#### F.7.19.40 getInitiatorAddressSpaceRefByName

Description: Returns the addressSpace referenced from the given initiator element.

— Returns: addressSpace of type String - The referenced addressSpace name
— Input: initiatorID of type String - Handle to a busInterface initiator element

#### F.7.19.41 getInitiatorAddressSpaceRefID

Description: Returns the addressSpaceRef defined on the given busInterface initiator element.

— Returns: addressSPaceRefID of type String - Handle to the addressSpaceRef element
— Input: initiatorID of type String - Handle to an initiator element

#### F.7.19.42 getMemoryMapRefModeRefByID

Description: Returns the handle to the mode referenced from the given memoryMapRef element.

— Returns: modeID of type String - Handle to the referenced mode element
— Input: memoryMapRefID of type String - Handle to a memoryMapRef element
— Input: modeRef of type String - The referenced mode

#### F.7.19.43 getMemoryMapRefModeRefByNames

Description: Returns all the modeRefs defined on the given memoryMapRef element.

— Returns: modeRefs of type String - List of the referenced modes
— Input: memoryMapRefID of type String - Handle to a memoryMapRef element

#### F.7.19.44 getMirroredSystemGroup

Description: Returns the group defined on the given mmirroredSystem element

— Returns: group of type String - The group value on the mirroredSystem element
— Input: mirroredSystemID of type String - Handle to a mirroredSystem element

#### F.7.19.45 getMirroredTargetBaseAddressesID

Description: Returns the handle to baseAddresses defined on the given mirroredTarget element.

— Returns: baseAddressesID of type String - Handle to a baseAddresses element
— Input: mirroredTargetID of type String - Handle to a mirroredTarget element

#### F.7.19.46 getMonitorGroup

Description: Returns the group defined on the given busInterface monitor element.

— Returns: group of type String - The group name
— Input: monitorID of type String - Handle to a monitor element

#### F.7.19.47 getRemapAddressModeRefByID

Description: Returns the handle to the mode referenced from the given remapAddress element.

— Returns: modeID of type String - Handle to the referenced mode element
— Input: remapAddressID of type String - Handle to a remapAddress element

#### F.7.19.48 getRemapAddressesRemapAddressID

Description: Returns the handle to remapAddress from the given remapAddresses element.

— Returns: remapAddressID of type String - Handle to a remapAddress element
— Input: remapAddressesID of type String - Handle to a remapAddresses element

#### F.7.19.49 getSystemGroup

Description: Returns the group defined on the given busInterface system element.

— Returns: group of type String - The group name
— Input: systemID of type String - Handle to a system element

#### F.7.19.50 getTargetFileSetRefGroupIDs

Description: Returns the handles to all the fileSetRefgroups defined on the given target element.

— Returns: fileSetRefgroupIDs of type String - List of handles to the fileSetRefGroup elements
— Input: targetID of type String - Handle to a busInterface target element

#### F.7.19.51 getTargetMemoryMapRefByName

Description: Returns the memoryMapRef defined on the given target element.

— Returns: memoryMapRef of type String - The memoryMap reference
— Input: targetID of type String - Handle to a target element of a busInterface

#### F.7.19.52 getTargetMemoryMapRefID

Description: Returns the handle to the memoryMapRef defined on the given target element.

— Returns: memoryMapRefID of type String - Handle to the memoryMapRef element
— Input: targetID of type String - Handle to a busInterface target element

#### F.7.19.53 getTargetTransparentBridgeIDs

Description: Returns the handles to all the transparentBridges defined on the given target element.

— Returns: transparentBrigesIDs of type String - List of handles to the transparentBridge ele-

ments

— Input: targetID of type String - Handle to a busInterface target element

### F.7.20 Bus interface (EXTENDED)

#### F.7.20.1 addAbstractionTypePortMap

Description: Adds a portMap with the given name, logicalPortName, and physicalPortName to the given
abstractionType

— Returns: portMapID of type String - Handle to a new portMap element
— Input: abstractionTypeID of type String - Handle to an abstractionType element
— Input: logicalPortName of type String - Logical port name
— Input: physicalPortName of type String - Physical port name

#### F.7.20.2 addAbstractionTypeViewRef

Description: Adds a viewRef with the given name to the given abstractionType element.

— Returns: viewRefID of type String - the viewRef identifier
— Input: abstractionTypeID of type String - Handle to an abstractionType element
— Input: viewRef of type String - View name

#### F.7.20.3 addAddressSpaceRefModeRef

Description: Adds an mode reference on an addressSpaceRef element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressSpaceRefID of type String - Handle to an addressSpaceRef element
— Input: modeRef of type String - The modeRef expression to be added on an addressSpaceRef element

#### F.7.20.4 addBaseAddressesRemapAddresses

Description: Adds a remapAddress on a baseAddresses element

— Returns: remapAddressesID of type String - Handle to a remapAddresses element
— Input: baseAddressesID of type String - Handle to a baseAddresses element
— Input: remapAddress of type String - The remapAddress value to be set on the remapAddresses element

#### F.7.20.5 addBusInterfaceAbstractionType

Description: Adds an abstractionType with the given abstractionRef to the given busInterface element.

— Returns: abstractionTypeID of type String - Handle to a new abstractionType element
— Input: busInterfaceID of type String - Handle to a busInterface element
— Input: abstractionRef of type String[] - AbstractionDef VLNV

#### F.7.20.6 addChannelBusInterfaceRef

Description: Adds a busInterfaceRef with the given name to the given channel element.

— Returns: busInterfaceRefID of type String - Handle to busInterfaceRef element
— Input: channelID of type String - Handle to a channel element
— Input: name of type String - BusInterface name

#### F.7.20.7 addMemoryMapRefModeRef

Description: Adds a modeRef on the given memoryMapRef element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: memoryMapRefID of type String - Handle to a memoryMapRef element
— Input: modeRef of type String - The mode reference to be add on the memoryMapRef element

#### F.7.20.8 addTargetFileSetRefGroup

Description: Adds a fileSetRefGroup on the given target element

— Returns: fileSetRefGroupID of type String - Handle to a fileSetRefGroup element
— Input: targetID of type String - Handle to a target element of a busInterface

#### F.7.20.9 addTargetTransparentBridge

Description: Adds a transparentBridge on the given target element

— Returns: transparentBridgeID of type String - Handle of a transparentBrige element
— Input: targetID of type String - Handle to a target element of a busInterface
— Input: initiatorRef of type String - The initiator reference value to be added

#### F.7.20.10 removeAbstractionTypePortMap

Description: Removes the given portMap element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: portMapID of type String - Handle to a portMap element

#### F.7.20.11 removeAbstractionTypeViewRef

Description: Removes the viewRef element with the given viewRef ID.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: viewRefID of type String - Handle of the viewRef

#### F.7.20.12 removeAddressSpaceRefBaseAddress

Description: Removes the baseAddress from the given addressSpaceRef element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressSpaceRefID of type String - Handle to an addressSpaceRef element

#### F.7.20.13 removeAddressSpaceRefModeRef

Description: Removes the designated modeRef from the given addressSpaceRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressSpaceRefID of type String - Handle to an addressSpaceRef element
— Input: modeRef of type String - The mode reference to be removed

#### F.7.20.14 removeBaseAddressesRemapAddresses

Description: Removes a remapAddresses element from a baseAddresses element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: remapAddressesID of type String - Handle to a remapAddresses element

#### F.7.20.15 removeBusDefinitionSystemGroupName

Description: Removes the given systemGroupName from its containing busDefinition element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: systemGroupNameID of type String - Handle to the systemGroupName to remove

#### F.7.20.16 removeBusInterfaceAbstractionType

Description: Removes the given abstractionType element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionTypeID of type String - Handle to an abstractionType element

#### F.7.20.17 removeBusInterfaceBitSteering

Description: Removes bitSteering from the given busInterface element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: busInterfaceID of type String - Handle to a busInterface element

#### F.7.20.18 removeBusInterfaceBitsInLau

Description: Removes the bitsInLau for the given busInterface element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: busInterfaceID of type String - Handle to an busInterface element

#### F.7.20.19 removeBusInterfaceConnectionRequired

Description: Removes connectionRequired from the given busInterface element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: busInterfaceID of type String - Handle to a busInterface element

#### F.7.20.20 removeBusInterfaceEndianness

Description: Removes endianness from the given busInterface element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: busInterfaceID of type String - Handle to a busInterface element

#### F.7.20.21 removeChannelBusInterfaceRef

Description: remove the selected busInterfaceRef from the Channel element if busInterfaceRef list size is
greater than 2.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: busInterfaceRefID of type String - Handle to a busInterfaceRef element

#### F.7.20.22 removeFileSetRefGroupGroup

Description: Removes the group on the given fileSetRefGroup element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileSetRefGroupID of type String - Handle to a fileSetRefGroup element

#### F.7.20.23 removeIndirectInterfaceBitsInLau

Description: Removes the bitsInLau for the given indirectInterface element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectInterfaceID of type String - Handle to an indirectInterface element

#### F.7.20.24 removeInitiatorAddressSpaceRef

Description: Removes the addressSpaceRef from an initiator element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: initiatorID of type String - Handle to an initiator element of a busInterface

#### F.7.20.25 removeMemoryMapRefModeRef

Description: Removes a modeRef from the given memoryMapRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: memoryMapRefID of type String - Handle to a memoryMapRef element
— Input: modeRef of type String - The mode reference to be remove on the memoryMapRef element

#### F.7.20.26 removeMirroredTargetBaseAddresses

Description: Removes the baseAddresses from the given mirroredTarget element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: mirroredTargetID of type String - Handle to a mirroredTarget element

#### F.7.20.27 removeMonitorGroup

Description: Removes the group on the given monitor element of a busInterface.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: monitorID of type String - Handle to a monitor element of a busInterface

#### F.7.20.28 removeTargetFileSetRefGroup

Description: Removes a fileSetRefGroup element from the given target element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileSetRefGroupID of type String - Handle to a fileSetRefGroup

#### F.7.20.29 removeTargetMemoryMapRef

Description: Removes the memoryMap reference on a target element of a bus interface.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: targetID of type String - Handle to a target element of a busInterface

#### F.7.20.30 removeTargetTransparentBridge

Description: Removes a transparentBridge element from the given target element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: transparentBrigeID of type String - Handle to a transparentBrige element

#### F.7.20.31 setAddressSpaceRefBaseAddress

Description: Sets the baseAddress on an addressSpaceRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressSpaceRefID of type String - Handle to an addressSpaceRef element
— Input: baseAddress of type String - The baseAddress expression to be set

#### F.7.20.32 setBaseAddressesRange

Description: Sets the range on a baseAddress element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: baseAddressesID of type String - Handle to a baseAddresses element
— Input: range of type String - the new range to set

#### F.7.20.33 setBusInterfaceBitSteering

Description: Sets bitSteering with the given value for the given busInterface element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: busInterfaceID of type String - Handle to a busInterface element
— Input: value of type String - BitSteering value

#### F.7.20.34 setBusInterfaceBitsInLau

Description: Sets the given bitsInLau expression for the busInterface element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: busInterfaceID of type String - Handle to an busInterface element
— Input: bitsInLau of type String - The bitsInLau expression

#### F.7.20.35 setBusInterfaceBusType

Description: Sets the busType on a busInterface element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: busInterfaceID of type String - Handle to an busInterface element
— Input: vlnv of type String[] - The vlnv expression to be set on the busType

#### F.7.20.36 setBusInterfaceConnectionRequired

Description: Sets connectionRequired with the given value for the given busInterface element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: busInterfaceID of type String - Handle to a busInterface element
— Input: value of type Boolean - ConnectionRequired value

#### F.7.20.37 setBusInterfaceEndianness

Description: Sets endianness with the given value for the given busInterface element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: busInterfaceID of type String - Handle to a busInterface element
— Input: endianness of type String - Endianness value : little or big

#### F.7.20.38 setBusInterfaceInitiator

Description: Sets the bus interface mode to initiator.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: busInterfaceID of type String - Handle to an busInterface element

#### F.7.20.39 setBusInterfaceMirroredInitiator

Description: Sets the bus interface mode to mirroredInitiator.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: busInterfaceID of type String - Handle to an busInterface element

#### F.7.20.40 setBusInterfaceMirroredSystem

Description: Sets the bus interface mode to mirroredSystem.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: busInterfaceID of type String - Handle to an busInterface element
— Input: group of type String - The group value to be set on the system element

#### F.7.20.41 setBusInterfaceMirroredTarget

Description: Sets the bus interface mode to mirroredTarget.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: busInterfaceID of type String - Handle to an busInterface element

#### F.7.20.42 setBusInterfaceMonitor

Description: Sets the bus interface mode to monitor.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: busInterfaceID of type String - Handle to an busInterface element
— Input: interfaceMode of type String - The interfaceMode value to be set on the monitor element

#### F.7.20.43 setBusInterfaceRefLocalName

Description: Returns the element localName on a busInterfaceRef of a channel element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: busInterfaceRefID of type String - Handle to the identifier to a busInterfaceRef element
— Input: name of type String - BusInterface name

#### F.7.20.44 setBusInterfaceSystem

Description: Sets the bus interface mode to system.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: busInterfaceID of type String - Handle to an busInterface element
— Input: group of type String - The group value to be set on the system element

#### F.7.20.45 setBusInterfaceTarget

Description: Sets the bus interface mode to target.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: busInterfaceID of type String - Handle to an busInterface element
— Input: memoryMapRef of type String - The memoryMap reference set on the target element

#### F.7.20.46 setFileSetRefGroupGroup

Description: Sets the group on the given fileSetRefGroup element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileSetRefGroupID of type String - Handle to a fileSetRefGroup element
— Input: group of type String - The group value to be set on the fileSetRefGroup element

#### F.7.20.47 setFileSetRefLocalName

Description: Sets the localName on a fileSetRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileSetRefID of type String - Handle to a fileSetRef element
— Input: localName of type String - The local Name value to be set

#### F.7.20.48 setIndirectInterfaceBitsInLau

Description: Sets the given bitsInLau expression for the indirectInterface element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectInterfaceID of type String - Handle to an indirectInterface element
— Input: bitsInLau of type String - BitsInLau expression

#### F.7.20.49 setInitiatorAddressSpaceRef

Description: Sets the addressSpaceRef on an initiator element of a busInterface.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: initiatorID of type String - Handle to an initiator element of a busInterface
— Input: addressSpaceRef of type String - The addressSpace reference to be set on the initiator element

#### F.7.20.50 setMirroredSystemGroup

Description: Sets the group on the given mmirroredSystem element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: mirroredSystemID of type String - Handle to a mirroredSystem element
— Input: group of type String - The group value to be set

#### F.7.20.51 setMirroredTargetBaseAddresses

Description: Sets the baseAddresses for the given mirroredTarget element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: mirroredTargetID of type String - Handle to a mirroredTarget element
— Input: remapAddress of type String - The new remapAddress expression
— Input: range of type String - The new range expression

#### F.7.20.52 setMonitorGroup

Description: Sets the group on the given monitor element of a busInterface.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: monitorID of type String - Handle to a monitor element of a busInterface
— Input: group of type String - The group value to be set

#### F.7.20.53 setRemapAddressesRemapAddress

Description: Sets the remapAddress from the given remapAddresses element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: remapAddressesID of type String - Handle to a remapAddresses element
— Input: remapAddress of type String - The remapAddress value to be set

#### F.7.20.54 setSystemGroup

Description: Sets the group on a system element of a busInterface.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: systemID of type String - Handle to a system element of a busInterface
— Input: group of type String - The group value to be set

#### F.7.20.55 setTargetMemoryMapRef

Description: Sets the memoryMap reference on a target element of a bus interface.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: targetID of type String - Handle to a target element of a busInterface
— Input: memoryMapRef of type String - The memoryMap reference to be set

### F.7.21 CPU (BASE)

#### F.7.21.1 getCpuAddressUnitBits

Description: Returns the addressUnitBits value defined on the given cpu element.

— Returns: addressUnitBits of type Long - The addressUnitBits value
— Input: cpuID of type String - Handle to a cpu element

#### F.7.21.2 getCpuAddressUnitBitsExpression

Description: Returns the addressUnitBits expression defined on the given cpu element.

— Returns: addressUnitBits of type String - The addressUnitBits expression
— Input: cpuID of type String - Handle to a cpu element

#### F.7.21.3 getCpuAddressUnitBitsID

Description: Returns the handle to the addressUnitBits defined on the given cpu element.

— Returns: addressUnitBitsID of type String - Handle to the addressUnitBits element
— Input: cpuID of type String - Handle to a cpu element

#### F.7.21.4 getCpuExecutableImageIDs

Description: Returns the handles to all the executableImages defined on the given cpu element.

— Returns: executableImageIDs of type String - List of handles to the executableImage elements

— Input: cpuID of type String - Handle to a cpu element

#### F.7.21.5 getCpuMemoryMapRefByID

Description: Returns the handle to the memoryMap referenced from the given cpu element.

— Returns: memoryMapID of type String - Handle to the referenced memoryMap element
— Input: cpuID of type String - Handle to a cpu element

#### F.7.21.6 getCpuMemoryMapRefByName

Description: Returns the memoryMap referenced from the given cpu element.

— Returns: memoryMapRef of type String - The referenced memoryMap
— Input: cpuID of type String - Handle to a cpu element

#### F.7.21.7 getCpuRange

Description: Returns the range value on a cpu element.

— Returns: range of type Long - The range value
— Input: cpuID of type String - Handle to a cpu element

#### F.7.21.8 getCpuRangeExpression

Description: Returns the range expression defined on the given cpu element.

— Returns: range of type String - The range expresion
— Input: cpuID of type String - Handle to a cpu element

#### F.7.21.9 getCpuRangeID

Description: Returns the handle to the range defined on the given cpu element.

— Returns: rangeID of type String - Handle to the range

— Input: cpuID of type String - Handle to a cpu element

#### F.7.21.10 getCpuRegionIDs

Description: Returns the handles to all the regions defined on the given cpu element.

— Returns: regionID of type String - List of handles to the region elements
— Input: cpuID of type String - Handle to a cpu element

#### F.7.21.11 getCpuWidth

Description: Returns the width value defined on the given cpu element.

— Returns: width of type Long - The width value
— Input: cpuID of type String - Handle to a cpu element

#### F.7.21.12 getCpuWidthExpression

Description: Returns the width expression defined on the given cpu element.

— Returns: width of type String - The width expression
— Input: cpuID of type String - Handle to a cpu element

#### F.7.21.13 getCpuWidthID

Description: Returns the handle to the width defined on the given cpu element.

— Returns: widthID of type String - Handle to the width element
— Input: cpuID of type String - Handle to a cpu element

### F.7.22 CPU (EXTENDED)

#### F.7.22.1 addCpuExecutableImage

Description: Adds an executable image on a cpu element.

— Returns: ExecutableImageID of type String - the executable image identifier
— Input: cpuID of type String - Handle of a cpu element
— Input: name of type String -The name to set on the executableImage
— Input: imageId of type String - The imageId attribute to set on the executableImage

#### F.7.22.2 addCpuRegion

Description: Adds a region on a cpu element.

— Returns: regionID of type String - the region identifier
— Input: cpuID of type String - Handle to a cpu element
— Input: name of type String - The name of the region
— Input: addressOffset of type String - The addressOffset expression of the region
— Input: range of type String - The range expression of the region

#### F.7.22.3 removeCpuAddressUnitBits

Description: Removes an addressUnitBits expression on a cpu element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)

— Input: cpuID of type String - Handle to a cpu element

#### F.7.22.4 removeCpuExecutableImage

Description: Removes the given executableImage from its containing cpu element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: executableImageID of type String - Handle to an executableImage element

#### F.7.22.5 removeCpuRegion

Description: Removes the given region from its containing cpu element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: regionID of type String - Handle of a region element

#### F.7.22.6 setCpuAddressUnitBits

Description: Sets an addressUnitBits expression on a cpu element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: cpuID of type String - Handle to a cpu element
— Input: addressUnitBits of type String - The addressunitBits expression to set

#### F.7.22.7 setCpuMemoryMapRef

Description: Sets the memoryMapRef of the cpu.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: cpuID of type String - Handle to a cpu element
— Input: value of type String - Name of the referenced memoryMap

#### F.7.22.8 setCpuRange

Description: Sets the range on a cpu element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: cpuID of type String - Handle to a cpu element
— Input: range of type String - The range value to set

#### F.7.22.9 setCpuWidth

Description: Sets the width expression on a cpu element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: cpuID of type String - Handle to a cpu element
— Input: width of type String - The width expression to set

#### F.7.22.10 setRegionAddressOffset

Description: Sets the addressOffset expression on a region element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: regionID of type String - Handle of a region element
— Input: addressOffset of type String - The addressOffset expression

#### F.7.22.11 setRegionRange

Description: Sets the range expression on a region element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: regionID of type String - Handle of a region element
— Input: range of type String - the range expression to set

### F.7.23 Catalog (BASE)

#### F.7.23.1 getCatalogAbstractionDefIpxactFileIDs

Description: Returns the handles to all the abstractionDefinitions files defined on the given catalog element.

— Returns: ipxactFileIDs of type String - List of handles to the ipxactFile elements
— Input: catalogID of type String - Handle to a catalog element

#### F.7.23.2 getCatalogAbstractorsIpxactFileIDs

Description: Returns the handles to all the abstractors files defined on the given catalog element.

— Returns: ipxactFileIDs of type String - List of handles to the ipxactFile elements
— Input: catalogID of type String - Handle to a catalog element

#### F.7.23.3 getCatalogBusDefinitionsIpxactFileIDs

Description: Returns the handles to all the busDefintions files defined on the given catalog element.

— Returns: ipxactFileIDs of type String - List of handles to the ipxactFile elements
— Input: catalogID of type String - Handle to a catalog element

#### F.7.23.4 getCatalogCatalogsIpxactFileIDs

Description: Returns the handles to all the IP-XACT files defined on the given catalog element.

— Returns: ipxactFileIDs of type String - List of handles to the ipxactFile elements
— Input: catalogID of type String - Handle to a catalog element

#### F.7.23.5 getCatalogComponentsIpxactFileIDs

Description: Returns the handles to all the components files defined on the given catalog element.

— Returns: ipxactFileIDs of type String - List of handles to the ipxactFile elements
— Input: catalogID of type String - Handle to a catalog element

#### F.7.23.6 getCatalogDesignConfigurationsIpxactFileIDs

Description: Returns the handles to all the designConfigurations files defined on the given catalog element.

— Returns: ipxactFileIDs of type String - List of handles to the ipxactFile elements
— Input: catalogID of type String - Handle to a catalog element

#### F.7.23.7 getCatalogDesignsIpxactFileIDs

Description: Returns the handles to all the designs files defined on the given catalog element.

— Returns: ipxactFileIDs of type String - List of handles to the ipxactFile elements

— Input: catalogID of type String - Handle to a catalog element

#### F.7.23.8 getCatalogGeneratorChainsIpxactFileIDs

Description: Returns the handles to all the generatorChains files defined on the given catalog element.

— Returns: ipxactFileIDs of type String - List of handles to the ipxactFile elements
— Input: catalogID of type String - Handle to a catalog element

#### F.7.23.9 getCatalogTypeDefinitionsIpxactFileIDs

Description: Returns the handles to all the typeDefinitions files defined on the given catalog element.

— Returns: ipxactFileIDs of type String - List of handles to the ipxactFile elements
— Input: catalogID of type String - Handle to a catalog element

#### F.7.23.10 getIpxactFileName

Description: Returns the file name of the given IP-XACT element.

— Returns: fileName of type String - File name ()
— Input: ipxactFileID of type String - Handle to an ipxactFile element

#### F.7.23.11 getIpxactFileVlnvRefByVLNV

Description: Returns the VLNV defined on the given ipxactFile element.

— Returns: VLNV of type String - The VLNV of the referenced IP-XACT file
— Input: ipxactFileID of type String - Handle to an ipxactFile element

### F.7.24 Catalog (EXTENDED)

#### F.7.24.1 addCatalogAbstractionDefIpxactFile

Description: Adds ipxactFile with the given VLNV and name to abstractionDefinitions in the given catalog
element.

— Returns: ipxactFileID of type String - Handle to an ipxactFile element
— Input: catalogID of type String - Handle to a catalog element
— Input: abstractionDefVLNV of type String[] - abstractionDef VLNV
— Input: fileName of type String - Abstraction definition file name

#### F.7.24.2 addCatalogAbstractorsIpxactFile

Description: Adds ipxactFile with the given VLNV and name to abstractors in the given catalog element.

— Returns: ipxactFileID of type String - Handle to an ipxactFile element
— Input: catalogID of type String - Handle to a catalog element
— Input: abstractorVLNV of type String[] - Abstractor VLNV
— Input: fileName of type String - Abstractor file name

#### F.7.24.3 addCatalogBusDefinitionsIpxactFile

Description: Adds ipxactFile with the given VLNV and name to busDefinitions in the given catalog element.

— Returns: ipxactFileID of type String - Handle to an ipxactFile element
— Input: catalogID of type String - Handle to a catalog element
— Input: busDefVLNV of type String[] - busDef VLNV
— Input: fileName of type String - Bus definition file name

#### F.7.24.4 addCatalogCatalogsIpxactFile

Description: Adds ipxactFile with the given VLNV and name to catalogs in the given catalog element.

— Returns: ipxactFileID of type String - Handle to an ipxactFile element
— Input: catalogID of type String - Handle to a catalog element
— Input: catalogVLNV of type String[] - Catalog VLNV
— Input: fileName of type String - Catalog file name

#### F.7.24.5 addCatalogComponentsIpxactFile

Description: Adds ipxactFile with the given VLNV and name to components in the given catalog element.

— Returns: ipxactFileID of type String - Handle to an ipxactFile element
— Input: catalogID of type String - Handle to a catalog element
— Input: componentVLNV of type String[] - Component VLNV
— Input: fileName of type String - Component file name

#### F.7.24.6 addCatalogDesignConfigurationsIpxactFile

Description: Adds ipxactFile with the given VLNV and name to designConfigurations in the given catalog
element.

— Returns: ipxactFileID of type String - Handle to an ipxactFile element
— Input: catalogID of type String - Handle to a catalog element
— Input: designConfigurationVLNV of type String[] - designConfiguration VLNV
— Input: fileName of type String - Design configuration file name

#### F.7.24.7 addCatalogDesignsIpxactFile

Description: Adds ipxactFile with the given VLNV and name to designs in the given catalog element.

— Returns: ipxactFileID of type String - Handle to an ipxactFile element
— Input: catalogID of type String - Handle to a catalog element
— Input: designVLNV of type String[] - Design VLNV
— Input: fileName of type String - Design file name

#### F.7.24.8 addCatalogGeneratorChainsIpxactFile

Description: Adds ipxactFile with the given VLNV and name to generatorChains in the given catalog
element.

— Returns: ipxactFileID of type String - Handle to an ipxactFile element
— Input: catalogID of type String - Handle to a catalog element
— Input: generatorChainVLNV of type String[] - generatorChain VLNV
— Input: fileName of type String - Generator chain file name

#### F.7.24.9 addCatalogTypeDefinitionsIpxactFile

Description: Adds ipxactFile with the given VLNV and name to typeDefinition in the given catalog element.

— Returns: ipxactFileID of type String - Handle to an ipxactFile element
— Input: catalogID of type String - Handle to a catalog element
— Input: typeDefinitionVLNV of type String[] - typeDefinition VLNV
— Input: fileName of type String - Generator chain file name

#### F.7.24.10 removeCatalogAbstractionDefIpxactFile

Description: Removes the given ipxactFile element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: ipxactFileID of type String - Handle to an ipxactFile element

#### F.7.24.11 removeCatalogAbstractorsIpxactFile

Description: Removes the given ipxactFile element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: ipxactFileID of type String - Handle to an ipxactFile element

#### F.7.24.12 removeCatalogBusDefinitionsIpxactFile

Description: Removes the given ipxactFile element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: ipxactFileID of type String - Handle to an ipxactFile element

#### F.7.24.13 removeCatalogCatalogsIpxactFile

Description: Removes the given ipxactFile element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: ipxactFileID of type String - Handle to an ipxactFile element

#### F.7.24.14 removeCatalogComponentsIpxactFile

Description: Removes the given ipxactFile element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: ipxactFileID of type String - Handle to an ipxactFile element

#### F.7.24.15 removeCatalogDesignConfigurationsIpxactFile

Description: Removes the given ipxactFile element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: ipxactFileID of type String - Handle to an ipxactFile element

#### F.7.24.16 removeCatalogDesignsIpxactFile

Description: Removes the given ipxactFile element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: ipxactFileID of type String - Handle to an ipxactFile element

#### F.7.24.17 removeCatalogGeneratorChainsIpxactFile

Description: Removes the given ipxactFile element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: ipxactFileID of type String - Handle to an ipxactFile element

#### F.7.24.18 removeCatalogTypeDefinitionsIpxactFile

Description: Removes the given ipxactFile element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: ipxactFileID of type String - Handle to an ipxactFile element

#### F.7.24.19 setIpxactFileName

Description: Sets the name for the given ipxactFile element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: ipxactFileID of type String - Handle to an ipxactFile element
— Input: name of type String - Name of the ipxactFile

#### F.7.24.20 setIpxactFileVlnv

Description: Sets the VLNV of the given ipxactFile element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: ipxactFileID of type String - Handle to an ipxactFile element
— Input: vlnv of type String[] - VLNV of the ipxactFile

### F.7.25 Choice (BASE)

#### F.7.25.1 getChoiceEnumerationIDs

Description: Returns the handles to all the choiceEnumerations defined on the given choice element.

— Returns: choiceEnumerationIDs of type String - List of handles to choiceEnumeration ele-

ments

— Input: choiceID of type String - Handle to a choice element

#### F.7.25.2 getEnumerationValue

Description: Returns the enumerationValue defined on the given enumeration element.

— Returns: enumerationValue of type String - The enumeration value
— Input: choiceEnumerationID of type String - Handle to an enumeration element

#### F.7.25.3 getEnumerationValueExpression

Description: Returns the expression defined on the given enumeration element.

— Returns: enumerationExpression of type String - The enumeration expression
— Input: choiceEnumerationID of type String - Handle to an enumeration element

### F.7.26 Choice (EXTENDED)

#### F.7.26.1 addChoiceEnumeration

Description: Adds enumeration with the given name to the given choice element.

— Returns: choiceEnumerationID of type String - Handle to a new choiceEnumeration
— Input: choiceID of type String - Handle to a choice element
— Input: name of type String - ChoiceEnumeration name

#### F.7.26.2 removeChoiceEnumeration

Description: Removes the given choiceEnumeration.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: choiceEnumerationID of type String - Handle to a choiceEnumeration element

#### F.7.26.3 setEnumerationValue

Description: Sets the value on the given enumeration element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: choiceEnumerationID of type String - Handle to the identifier of an enumeration ele-

ment

— Input: value of type String - New value expression

### F.7.27 Clearbox (BASE)

#### F.7.27.1 getClearboxElementClearboxType

Description: Returns the clearboxType element defined on the given clearboxElement.

— Returns: type of type String - The clearboxType value
— Input: clearboxElementID of type String - Handle to a clearboxElement element

#### F.7.27.2 getClearboxElementDriveable

Description: Returns the driveable element defined on the given clearboxElement.

— Returns: value of type Boolean - The driveable value
— Input: clearboxElementID of type String - Handle to a clearboxElement

#### F.7.27.3 getClearboxElementRefByID

Description: Returns the handle to the clearboxElement referenced from the name define on given
clearboxElementRef element.

— Returns: clearboxElementID of type String - Handle to the referenced clearboxElement
— Input: clearboxElementRefID of type String - Handle to a clearboxElementRef element

#### F.7.27.4 getClearboxElementRefLocationIDs

Description: Returns the handles to all the clearboxElementRefLocations defined on the given
clearboxElementRef element.

— Returns: clearboxElementRefLocationIDs of type String - List of handles to the clearboxElementRefLocation elements
— Input: clearboxElementRefID of type String - Handle to a clearboxElementRef element

### F.7.28 Clearbox (EXTENDED)

#### F.7.28.1 addClearboxElementRefLocation

Description: Adds a clearboxElementRefLocation element to a given clearboxElementRef element.

— Returns: clearboxElementRefLocationID of type String - Handle to the added clearbox- elementRefLocation

— Input: clearboxElementRefID of type String - Handle to a clearboxElementRef element
— Input: value of type String - value of the pathSegment

#### F.7.28.2 addLocationSlice

Description: Adds a slice to a given Location element.

— Returns: sliceID of type String - Handle to the added slice
— Input: locationID of type String - Handle to a location element
— Input: value of type String - Handle to value of the pathSegment

#### F.7.28.3 removeClearboxElementDriveable

Description: Removes driveable from the given clearBox element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: clearboxElementID of type String - Handle to a clearboxElement element

#### F.7.28.4 removeClearboxElementRefLocation

Description: Removes the given clearboxElementRefLocation element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: clearboxElementRefLocationID of type String - Handle to a clearboxElementRe-

fLocation element

#### F.7.28.5 setClearboxElementClearboxType

Description: Sets clearbox type.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: clearboxID of type String - Handle to a clearbox element
— Input: clearboxType of type String - clearbox type

#### F.7.28.6 setClearboxElementDriveable

Description: Sets driveable with the given value for the given clearBox element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: clearboxElementID of type String - Handle to a clearboxElement element
— Input: value of type Boolean - ClearboxElement driveable

### F.7.29 Component (BASE)

#### F.7.29.1 getComponentAddressSpaceIDs

Description: Returns the addressSpaceIDs defined on the given component object or component instance
element.

— Returns: addressSpaceIDs of type String - List of handles to the addressSpace elements
— Input: componentOrComponentInstanceID of type String - Handle to a component object

or componentInstance element

#### F.7.29.2 getComponentBusInterfaceIDs

Description: Returns the handles to all the busInterfaces defined on the given component object or
component instance element.

— Returns: busInterfaceIDs of type String - List of handles to the busInterface elements
— Input: componentOrComponentInstanceID of type String - Handle to a component object

or componentInstance element

#### F.7.29.3 getComponentChannelIDs

Description: Returns the channelIDs defined on the given component object or component instance element.

— Returns: channelIDs of type String - List of handles to the channel elements
— Input: componentOrComponentInstanceID of type String - Handle to a component object

or componentInstance element

#### F.7.29.4 getComponentChoiceIDs

Description: Returns the handles to all the choices defined on the given component object or component
instance element.

— Returns: choiceIDs of type String - List of handles to choice elements
— Input: componentOrComponentInstanceID of type String - Handle to a component object

or componentInstance element

#### F.7.29.5 getComponentClearboxElementIDs

Description: Returns the handles to all the clearboxElements defined on a given component or component
instance element.

— Returns: clearboxElementIDs of type String - List of handles to the clearboxElement ele-

ments

— Input: componentOrComponentInstanceID of type String - Handle to a component or com-

ponentInstance element

#### F.7.29.6 getComponentComponentGeneratorIDs

Description: Returns the handles to all the generators defined on the given component or component
instance element.

— Returns: generatorIDs of type String - List of handles to the generator elements
— Input: componentOrComponentInstanceID of type String - Handle to a component or componentInstance element

#### F.7.29.7 getComponentComponentInstantiationIDs

Description: Returns the handles to all the componentInstantiations defined on the given component object
or component instance element.

— Returns: componentInstantiationIDs of type String - List of handles to the componentIn-

stantiation elements

— Input: componentOrComponentInstanceID of type String - Handle to a component object

or componentInstance element

#### F.7.29.8 getComponentCpuIDs

Description: Returns the handles to all the cpus defined on the given component object or component
instance element.

— Returns: cpuIDs of type String - List of handles to the cpu elements
— Input: componentOrComponentInstanceID of type String - Handle to a component object

or componentInstance element

#### F.7.29.9 getComponentDesignConfigurationInstantiationIDs

Description: Returns the handles to all the designConfigurationInstantiations defined on the given
component or component instance element.

— Returns: designConfigurationInstantiationIDs of type String - List of handles to the

designConfigurationInstantiation elements

— Input: componentOrComponentInstanceID of type String - Handle to a component object

or componentInstance element

#### F.7.29.10 getComponentDesignInstantiationIDs

Description: Returns the handles to all the designInstantiations defined on the given component object or
component instance element.

— Returns: designInstantiationIDs of type String - List of handles to the designInstantiation elements

— Input: componentOrComponentInstanceID of type String - Handle to a component object

or componentInstance element

#### F.7.29.11 getComponentExternalTypeDefinitionsIDs

Description: Returns the handles to all the typeDefinitions defined on the given component object.

— Returns: externalTypeDefinitionsIDs of type String - List of handles to the typeDefini-

tion elements

— Input: componentID of type String - Handle to a component object

#### F.7.29.12 getComponentFileSetIDs

Description: Returns the handles to all the fileSets defined on the given component object or component
instance element.

— Returns: fileSetIDs of type String - List of handles to fileSet elements
— Input: componentOrComponentInstanceID of type String - Handle to a component object or componentInstance element

#### F.7.29.13 getComponentIndirectInterfaceIDs

Description: Returns the indirectInterfaceIDs defined on the given component object or component instance
element.

— Returns: indirectInterfaceIDs of type String - List of handles to the indirectInterface elements
— Input: componentOrComponentInstanceID of type String - Handle to a component object

or componentInstance element

#### F.7.29.14 getComponentMemoryMapIDs

Description: Returns the memoryMapIDs defined on the given component object or component instance
element.

— Returns: memoryMapIDs of type String - List of handles to the memoryMap elements
— Input: componentOrComponentInstanceID of type String - Handle to a component object

or componentInstance element

#### F.7.29.15 getComponentModeIDs

Description: Returns the handles to all the modes defined on the given component object

— Returns: modeIDs of type String - List of handles to the mode elements
— Input: componentID of type String - Handle to a component object

#### F.7.29.16 getComponentOtherClockDriverIDs

Description: Returns the handles to all the clockDrivers defined on the given component object or
component instance element.

— Returns: clockDriverIDs of type String - List of handles to the clockDriver elements
— Input: componentOrComponentInstanceID of type String - Handle to a component object

or componentInstance element

#### F.7.29.17 getComponentPortIDs

Description: Returns the handles to all the ports defined on the given component object or component
instance element.

— Returns: portIDs of type String - List of handles to port elements
— Input: componentOrComponentInstanceID of type String - Handle to a component object

or componentInstance element

#### F.7.29.18 getComponentPowerDomainIDs

Description: Returns the handles to all the powerDomains defined on the given component object.

— Returns: powerDomainIDs of type String - List of handles to the powerDomain elements
— Input: componentID of type String - Handle to a component object

#### F.7.29.19 getComponentResetTypeIDs

Description: Returns the handles to all the resetTypes defined on the given component object or component
instance element.

— Returns: resetTypeIDs of type String - List of handles to the resetType elements
— Input: componentOrComponentInstanceID of type String - Handle to a component object

or componentInstance element

#### F.7.29.20 getComponentSelectedViewIDs

Description: Returns the handles to the selected views defined on the given component object or component
instance element.

— Returns: viewIDs of type String - List of handles to the selected view elements
— Input: componentOrComponentInstanceID of type String - Handle to a component object

or componentInstance element

#### F.7.29.21 getComponentViewIDs

Description: Returns the viewIDs defined on the given component object or component instance element.

— Returns: viewIDs of type String - List of handles to the view elements
— Input: componentOrComponentInstanceID of type String - Handle to a component object

or componentInstance element

#### F.7.29.22 getModeCondition

Description: Returns the condition (resolved) value defined on the given component mode element.

— Returns: condition of type String - The mode condition value
— Input: modeID of type String - Handle to a mode element

#### F.7.29.23 getModeConditionExpression

Description: Returns the condition expression defined on the given component mode element.

— Returns: condition of type String - The mode condition expression
— Input: modeID of type String - Handle to a mode element

#### F.7.29.24 getModeName

Description: Returns the name of the given component mode element.

— Returns: name of type String - The mode name
— Input: modeID of type String - Handle to a mode element

### F.7.30 Component (EXTENDED)

#### F.7.30.1 addComponentAddressSpace

Description: Adds an addressSpace with the given name, range, and width to the given component element.

— Returns: addressSpaceID of type String - Handle to a new addressSpace
— Input: componentID of type String - Handle to a component element
— Input: name of type String - addressSpace name
— Input: range of type String - addressSpace range expression
— Input: width of type String - addrressSpace width expression

#### F.7.30.2 addComponentChannel

Description: Adds a channel with the given name and busInterfaceRefs to the given component element.

— Returns: channelID of type String - Handle to a new channel
— Input: componentID of type String - Handle to a component element
— Input: name of type String - Channel name
— Input: busInterfaceRefs of type String[] - List of busInterface names

#### F.7.30.3 addComponentChoice

Description: Adds a choice with the given name and enumerations to the given component element.

— Returns: choiceID of type String - Handle to a new choice
— Input: componentID of type String - Handle to a component element
— Input: name of type String - Choice name
— Input: enumerations of type String[] - List of enumeration values

#### F.7.30.4 addComponentClearboxElement

Description: Adds a clearboxElement with the given name and type to the given component element.

— Returns: clearboxElementID of type String - Handle to a new clearboxElement
— Input: componentID of type String - Handle to a component element
— Input: name of type String - ClearboxElement name
— Input: type of type String - Clearbox element type

#### F.7.30.5 addComponentComponentGenerator

Description: Adds a generator with the given name and path to the given component element.

— Returns: generatorID of type String - Handle to a new generator
— Input: componentID of type String - Handle to a component element
— Input: name of type String - Generator name
— Input: generatorExecutable of type String - Path to generator executable

#### F.7.30.6 addComponentComponentInstantiation

Description: Adds a componentInstantiation with the given name to the given component element.

— Returns: componentInstantiationID of type String - Handle to a new componentInstantia-

tion

— Input: componentID of type String - Handle to a component element
— Input: name of type String - ComponentInstantiation name

#### F.7.30.7 addComponentCpu

Description: Adds a cpu with the given name to the given element.

— Returns: cpuID of type String - Handle to the added cpu
— Input: componentID of type String - Handle to a component object
— Input: name of type String - The cpu name
— Input: memoryMapRef of type String - A ref to an memoryMap element
— Input: range of type String - The range expression to set
— Input: width of type String - The width expression to set

#### F.7.30.8 addComponentDesignConfigurationInstantiation

Description: Adds a designConfiguration
componentInstance element.

instantiation element

to

the given component or

— Returns: designConfigurationInstantiationID of type String - Handle of new design-

ConfigurationInstantiation

— Input: componentOrComponentInstanceID of type String - Handle to a component element
— Input: name of type String - designConfigurationInstantiation name
— Input: designConfigurationVLNV of type String[] - VLNV for a new designConfigurationIn-

stantiation

#### F.7.30.9 addComponentDesignInstantiation

Description: Adds a designInstantiation with the given name and designRef to the given component
element.

— Returns: designInstantiationID of type String - Handle to a new designInstantiation
— Input: componentID of type String - Handle to a component element
— Input: name of type String - DesignInstantiation name
— Input: designVLNV of type String[] - Design VLNV

#### F.7.30.10 addComponentFileSet

Description: Adds a fileSet with the given name to the given component element.

— Returns: fileSetID of type String - Handle to a new fileSet
— Input: componentID of type String - Handle to a component element
— Input: name of type String - FileSet name

#### F.7.30.11 addComponentIndirectInterface

Description: Adds an indirectInterface with the given name, indirectAddress, indirectData, memoryMapRef,
or busInterfaceRef to the given component element.

— Returns: indirectInterfaceID of type String - Handle to a new indirectInterface
— Input: componentID of type String - Handle to a component element
— Input: name of type String - The indirectInterface name
— Input: indirectAddressRef of type String - Set the fieldRef on the indirectAddressRef
— Input: indirectData of type String - The indirectData value
— Input: memoryMapRef of type String - Name of memoryMap or null

#### F.7.30.12 addComponentInitiatorBusInterface

Description: Adds a busInterface with the given name, busType, interfaceMode, and group to the given
component element.

— Returns: busInterfaceID of type String - Handle to a new busInterface
— Input: componentID of type String - Handle to a component element
— Input: name of type String - The busInterface name
— Input: busVLNV of type String[] - The busDef VLNV

#### F.7.30.13 addComponentMemoryMap

Description: Adds a memoryMap with the given name to the given component element.

— Returns: memoryMapID of type String - Handle to a new memoryMap
— Input: componentID of type String - Handle to a component element
— Input: name of type String - MemoryMap name

#### F.7.30.14 addComponentMirroredInitiatorBusInterface

Description: Adds a busInterface with the given name, busType, interfaceMode, and group to the given
component element.

— Returns: busInterfaceID of type String - Handle to a new busInterface
— Input: componentID of type String - Handle to a component element
— Input: name of type String - The busInterface name
— Input: busVLNV of type String[] - The busDef VLNV

#### F.7.30.15 addComponentMirroredSystemBusInterface

Description: Adds a busInterface with the given name, busType, interfaceMode, and group to the given
component element.

— Returns: busInterfaceID of type String - Handle to a new busInterface
— Input: componentID of type String - Handle to a component element
— Input: name of type String - The busInterface name
— Input: busVLNV of type String[] - The busDef VLNV
— Input: group of type String - Sets the group

#### F.7.30.16 addComponentMirroredTargetBusInterface

Description: Adds a busInterface with the given name, busType, interfaceMode, and group to the given
component element.

— Returns: busInterfaceID of type String - Handle to a new busInterface
— Input: componentID of type String - Handle to a component element
— Input: name of type String - The busInterface name
— Input: busVLNV of type String[] - The busDef VLNV

#### F.7.30.17 addComponentMode

Description: Adds a new mode to the given component.

— Returns: modeID of type String - The identifier of the added mode
— Input: componentID of type String - Handle to the component object
— Input: name of type String - Mode name

#### F.7.30.18 addComponentMonitorBusInterface

Description: Adds a busInterface with the given name, busType, interfaceMode, and group to the given
component element.

— Returns: busInterfaceID of type String - Handle to a new busInterface
— Input: componentID of type String - Handle to a component element
— Input: name of type String - busInterface name
— Input: busVLNV of type String[] - busDef VLNV
— Input: interfaceMode of type String - InterfaceMode attribute. Can be one of 'initiator', 'target',

'system', 'mirroredInitiator', 'mirroredTarget' or 'mirroredSystem'

#### F.7.30.19 addComponentOtherClockDriver

Description: Adds a clockDriver with the given name, period, offset, value, and duration to the given
component element.

— Returns: clockDriverID of type String - Handle to a new clockDriver
— Input: componentID of type String - Handle to a component element
— Input: name of type String - clockDriver name
— Input: periodExpression of type String - Clock period
— Input: offsetExpression of type String - Clock pulse offset
— Input: valueExpression of type String - Clock pulse value
— Input: durationExpression of type String - Clock pulse duration

#### F.7.30.20 addComponentResetType

Description: Adds a resetType with the given name to the given component element.

— Returns: resetTypeID of type String - Handle to a new resetType
— Input: componentID of type String - Handle to a component element
— Input: name of type String - resetType name

#### F.7.30.21 addComponentStructuredInterfacePort

Description: Adds a structured interface port with the given name and direction for the given component
element.

— Returns: portID of type String - Handle to a new port
— Input: componentID of type String - Handle to an component element
— Input: name of type String - Handle to a port by his name
— Input: structPortTypeDefTypeName of type String - The typeName of the structPortTy-

peDef

#### F.7.30.22 addComponentStructuredStructPort

Description: Adds a structured struct port with the given name and direction for the given component
element.

— Returns: portID of type String - Handle to a new port
— Input: componentID of type String - Handle to an component element
— Input: name of type String - Handle to a port by his name
— Input: structPortTypeDefTypeName of type String - The typeName of the structPortTypeDef
— Input: direction of type String - Value of the direction

#### F.7.30.23 addComponentStructuredUnionPort

Description: Adds a structured union port with the given name and direction for the given component
element.

— Returns: portID of type String - Handle to a new port
— Input: componentID of type String - Handle to an component element
— Input: name of type String - Handle to a port by his name
— Input: structPortTypeDefTypeName of type String - The typeName of the structPortTy-

peDef

— Input: subPortName of type String - The name of the subPort
— Input: direction of type String - Value of the direction

#### F.7.30.24 addComponentSystemBusInterface

Description: Adds a busInterface with the given name, busType, interfaceMode, and group to the given
component element.

— Returns: busInterfaceID of type String - Handle to a new busInterface
— Input: componentID of type String - Handle to a component element
— Input: name of type String - busInterface name
— Input: busVLNV of type String[] - busDef VLNV
— Input: group of type String - group name

#### F.7.30.25 addComponentTargetBusInterface

Description: Adds a busInterface with the given name, busType, interfaceMode, and group to the given
component element.

— Returns: busInterfaceID of type String - Handle to a new busInterface
— Input: componentID of type String - Handle to a component element
— Input: name of type String - busInterface name
— Input: busVLNV of type String[] - busDef VLNV

#### F.7.30.26 addComponentTransactionalPort

Description: Adds a transactional port with the given name and initiative to the given component element.

— Returns: portID of type String - Handle to a new port
— Input: componentID of type String - Handle to a component element
— Input: name of type String - Port name
— Input: initiative of type String - Port initiative

#### F.7.30.27 addComponentView

Description: Adds a view with the given name to the given component object.

— Returns: viewID of type String - Handle to the added view
— Input: componentID of type String - Handle to a component object
— Input: name of type String - View name

#### F.7.30.28 addComponentWirePort

Description: Adds a wire port with the given name and direction to the given component element.

— Returns: portID of type String - Handle to a new port
— Input: componentID of type String - Handle to a component element
— Input: name of type String - Port name
— Input: direction of type String - Port direction

#### F.7.30.29 removeComponentAddressSpace

Description: Removes the given addressSpace element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressSpaceID of type String - Handle to an addressSpace element

#### F.7.30.30 removeComponentBusInterface

Description: Removes the given busInterface element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: busInterfaceID of type String - Handle to a busInterface element

#### F.7.30.31 removeComponentChannel

Description: Removes the given channel element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: channelID of type String - Handle to a channel element

#### F.7.30.32 removeComponentChoice

Description: Removes the given choice element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: choiceID of type String - Handle to a choice element

#### F.7.30.33 removeComponentClearboxElement

Description: Removes the given clearboxElement element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: clearboxElementID of type String - Handle to a clearboxElement element

#### F.7.30.34 removeComponentComponentGenerator

Description: Removes the given generator element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: generatorID of type String - Handle to a generator element

#### F.7.30.35 removeComponentComponentInstantiation

Description: Removes the given componentInstantiation element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)

— Input: componentInstantiationID of type String - Handle to a componentInstantiation ele-

ment

#### F.7.30.36 removeComponentCpu

Description: Removes the given cpu element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: cpuID of type String - Handle to a cpu

#### F.7.30.37 removeComponentDesignConfigurationInstantiation

Description: Removes the given designConfigurationInstantiation element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: designConfigurationInstantiationID of type String - Handle to a

designConfigurationInstantiation element

#### F.7.30.38 removeComponentDesignInstantiation

Description: Removes the given designInstantiation element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: designInstantiationID of type String - Handle to a designInstantiation element

#### F.7.30.39 removeComponentFileSet

Description: Removes the given fileSet element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileSetID of type String - Handle to a fileSet element

#### F.7.30.40 removeComponentIndirectInterface

Description: Removes the given indirectInterface element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectInterfaceID of type String - Handle to an indirectInterface element

#### F.7.30.41 removeComponentMemoryMap

Description: Removes the given memoryMap element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: memoryMapID of type String - Handle to a memoryMap element

#### F.7.30.42 removeComponentMode

Description: Removes the given mode from its containing component object.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: modeID of type String - Handle to the modeID

#### F.7.30.43 removeComponentOtherClockDriver

Description: Removes the given clockDriver element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: clockDriverID of type String - Handle to a clockDriver element

#### F.7.30.44 removeComponentPort

Description: Removes the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: portID of type String - Handle to a port element

#### F.7.30.45 removeComponentResetType

Description: Removes the given resetType element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: resetTypeID of type String - Handle to a resetType element

#### F.7.30.46 removeComponentView

Description: Removes the given view element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: viewID of type String - Handle to a view element

#### F.7.30.47 removeMemoryMapAddressUnitBits

Description: Removes the addressUnitBits on a memoryMap or memoryMapDefinition element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: memoryMapID of type String - the memoryMap or memoryMapDefinition identifier

#### F.7.30.48 removeModeCondition

Description: Removes the condition associated with the given mode on a component.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: modeID of type String - Handle to the mode type

#### F.7.30.49 removePowerDomainAlwaysOn

Description: Removes alwaysOn from a powerDomain element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: powerDomainID of type String - Handle to a powerDomain element

#### F.7.30.50 setIndirectInterfaceIndirectAddressRef

Description: set an indirectAddressRef node on an indirectInterface element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectInterfaceID of type String - Handle to an indirectInterface element
— Input: fieldRef of type String - Set the fieldRef on the indirectAddressRef element

#### F.7.30.51 setIndirectInterfaceIndirectDataRef

Description: set an indirectDataRef node on an indirectInterface element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectInterfaceID of type String - Handle to an indirectInterface element
— Input: fieldRef of type String - Set the fieldRef on the indirectAddressRef element

#### F.7.30.52 setMemoryMapAddressUnitBits

Description: Sets the addressUnitBits on a memoryMap or memoryMapDefinition element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: memoryMapID of type String - the memoryMap or memoryMapDefinition identifier
— Input: addressUnitBit of type String - the addressUnitBit value to be added

#### F.7.30.53 setModeCondition

Description: Sets the name associated with the given mode on a component.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: modeID of type String - Handle to the mode type
— Input: condition of type String - Handle to value of the condition of type String

#### F.7.30.54 setModeName

Description: Sets the name associated with the given mode on a component.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: modeID of type String - Handle to the mode type
— Input: name of type String - Handle to value of the name of type String

### F.7.31 Configurable element (BASE)

#### F.7.31.1 getConfigurableElementIDs

Description: Returns the handles to all the configurableElements defined on the given unconfigured
element.

— Returns: configurableElementIDs of type String - List of handes to configurable elements
— Input: unconfiguredElementID of type String - Handle to an unconfigured element

#### F.7.31.2 getConfigurableElementValue

Description: Returns the default value defined on the given configurable element.

— Returns: value of type String - The default configurable element value
— Input: configurableElementID of type String - Handle to a configurable element

#### F.7.31.3 getConfigurableElementValueExpression

Description: Returns the default expression defined on the given configurable element.

— Returns: expression of type String - The default configurable element expression
— Input: configurableElementID of type String - Handle to a configurable element

#### F.7.31.4 getConfigurableElementValueIDs

Description: Returns the handles to all the configurableElementValues defined on the given configured
element.

— Returns: configurableElementValueIDs of type String - List of handles to configurableElementValue elements
— Input: configuredElementID of type String - Handle to a configured element

#### F.7.31.5 getConfigurableElementValueReferenceID

Description: Returns the referenceId attribute defined on the given configurable element value.

— Returns: referenceId of type String - The referenceId value
— Input: configurableElementValueID of type String - Handle to a configurable element

value

#### F.7.31.6 getConfigurableElementValueValueExpression

Description: Returns the expression defined on the given configurable element value.

— Returns: expression of type String - The expression defined on the configurable element value
— Input: configurableElementValueID of type String - Handle to a configurable element

value

#### F.7.31.7 getUnconfiguredID

Description: Returns the handle to the unconfigured element corresponding to the given configured element.

— Returns: unconfiguredElementID of type String - Handle to the corresponding unconfigured element

— Input: configuredElementID of type String - Handle to a configured element

### F.7.32 Configurable element (EXTENDED)

#### F.7.32.1 addConfigurableElementValue

Description: Adds a configurable element value with the given expression to the given configured element
and the given referenceID.

— Returns: configurableElementValueID of type String - Handle to new

configurableElementValue

— Input: configuredElementID of type String - Handle to a configured element
— Input: referenceID of type String - Reference to a configurable element
— Input: expression of type String - New expression

#### F.7.32.2 addViewConfigurationConfigurableElementValue

Description: Adds a configurable element value with the given expression to the given configured element
and the given referenceID.

— Returns: configurableElementValueID of type String - Handle to new

configurableElementValue

— Input: viewConfigurationID of type String - Handle of a viewConfiguration
— Input: referenceID of type String - Reference to a configurable element
— Input: expression of type String - New expression

#### F.7.32.3 removeConfigurableElementValue

Description: Removes the given configurable element value.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: configurableElementValueID of type String - Handle to a configurable element

value

#### F.7.32.4 setConfigurableElementValue

Description: Sets the value of a given configurable element (default value).

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: configurableElementID of type String - Handle to a configurable element
— Input: expression of type String - New expression

#### F.7.32.5 setConfigurableElementValueReferenceID

Description: Sets the given referenceID for the given configurable element value.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: configurableElementValueID of type String - Handle to a configurable element

value

— Input: referenceID of type String - New referenceID

#### F.7.32.6 setConfigurableElementValueValue

Description: Sets the given expression as value for the given configurable element value.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: configurableElementValueID of type String - Handle to a configurable element

value

— Input: expression of type String - New expression

### F.7.33 Constraint (BASE)

#### F.7.33.1 getCellSpecificationCellClass

Description: Returns the cellClass value defined on the given cellSpecification element.

— Returns: cellClassID of type String - The cellClass value
— Input: cellSpecificationID of type String - Handle to a cellSpecification element

#### F.7.33.2 getCellSpecificationCellFunction

Description: Returns the cellFunction value defined on the given cellSpecification element.

— Returns: cellFunction of type String - The cellFunction value
— Input: cellSpecificationID of type String - Handle to a cellSpecification element

#### F.7.33.3 getCellSpecificationCellFunctionID

Description: Returns the handle to the cellFunction defined on the given cellSpecification element.

— Returns: cellFunctionID of type String - Handle to the cellFunction element
— Input: cellSpecificationID of type String - Handle to a cellSpecification element

#### F.7.33.4 getConstraintSetDriveConstraintCellSpecificationID

Description: Returns the handle to the cellSpecification defined on the given constraintSet element.

— Returns: cellSpecificationID of type String - Handle to the cellSpecification element
— Input: constraintSetID of type String - Handle to a constraintSet element

#### F.7.33.5 getConstraintSetLoadConstraintID

Description: Returns the handle to the loadConstraint defined on the given constraintSet element.

— Returns: loadConstraintID of type String - Handle to the loadConstraint element
— Input: constraintSetID of type String - Handle to a constraintSet element

#### F.7.33.6 getConstraintSetRefLocalName

Description: Returns the locaName defined on the given constraintSetRefRef element.

— Returns: localName of type String - The local name
— Input: constraintSetRefID of type String - Handle to a constraintSetRef element

#### F.7.33.7 getConstraintSetReferenceName

Description: Returns the value of the constraintSetId attribute defined on the given constraintSet element.

— Returns: referenceName of type String - The constraintSetId attribute value
— Input: constraintSetID of type String - Handle to a constraintSet element

#### F.7.33.8 getConstraintSetTimingConstraintIDs

Description: Returns the handles to all the timingConstraints defined on the given constraintSet.

— Returns: timingConstraintIDs of type String - List of handles to the timingConstraint elements

— Input: constraintSetID of type String - Handle to a constraintSet element

#### F.7.33.9 getConstraintSetVector

Description: Returns the range defined on the given constraintSet.

— Returns: range of type Long - Array of two range values: left and right
— Input: constraitSetID of type String - Handle to a constraintSet element

#### F.7.33.10 getConstraintSetVectorExpression

Description: Returns the vector left and right expressions defined on the given constraintSet element.

— Returns: range of type String - Array of two vector expressions: left and right
— Input: constraintSetID of type String - Handle to a constraintSet element

#### F.7.33.11 getConstraintSetVectorLeftID

Description: Returns the handle to the left side of the vector defined on the given constraintSet element.

— Returns: leftID of type String - Handle to the left element
— Input: constraintSetID of type String - Handle to a constraintSet element

#### F.7.33.12 getConstraintSetVectorRightID

Description: Returns the handle to the right side of the vector defined on the given constraintSet element.

— Returns: rightID of type String - Handle to the right element
— Input: constraintSetID of type String - Handle to a constraintSet element

#### F.7.33.13 getDriveConstraintOther

Description: Returns the other attribute value defined on the given driveConstraint (cellFunction only).

— Returns: value of type String - The value of the other attribute
— Input: driveConstraintID of type String - Handle to a driveConstraint element

#### F.7.33.14 getDriveConstraintType

Description: Returns the type defined on the given driveConstraint element.

— Returns: value of type String - The drive constraint type
— Input: driveConstraintID of type String - Handle to a driveConstraint element

#### F.7.33.15 getDriveConstraintValue

Description: Returns the value defined on the given driveConstraint element.

— Returns: value of type String - The drive constraint value
— Input: driveConstraintID of type String - Handle to a driveConstraint element

#### F.7.33.16 getLoadConstraintCellSpecificationID

Description: Returns the handle to the cellSpecification defined on the given loadConstraint element.

— Returns: cellSpecificationID of type String - Handle to the cellSpecification element
— Input: loadConstraintID of type String - Handle to a loadConstraint element

#### F.7.33.17 getLoadConstraintCount

Description: Returns the count defined on the given loadConstraint element.

— Returns: value of type Long - The load constraint count
— Input: loadConstraintID of type String - Handle to a loadConstraint element

#### F.7.33.18 getLoadConstraintCountExpression

Description: Returns the count expression defined on the given loadConstraint element.

— Returns: expression of type String - The load constraint count
— Input: loadConstraintID of type String - Handle to a loadConstraint element

#### F.7.33.19 getLoadConstraintCountID

Description: Returns the handle to the count element defined on the given loadConstraint element.

— Returns: countID of type String - Handle to the count element
— Input: loadConstraintID of type String - Handle to a loadConstraint element

#### F.7.33.20 getLoadConstraintOther

Description: Returns the other attribute value defined on the given loadConstraint (cellFunction only).

— Returns: value of type String - The value of the other attribute
— Input: loadConstraintID of type String - Handle to a loadConstraint element

#### F.7.33.21 getLoadConstraintType

Description: Returns the type defined on the given loadConstraint element.

— Returns: value of type String - The load constraint type
— Input: loadConstraintID of type String - Handle to a loadConstraint element

#### F.7.33.22 getLoadConstraintValue

Description: Returns the value defined on the given loadConstraint element.

— Returns: value of type String - The load constraint value
— Input: loadConstraintID of type String - Handle to a loadConstraint element

#### F.7.33.23 getTimingConstraintValue

Description: Returns the value defined on the given timingConstraint element.

— Returns: value of type Float - The constraint value (in cycle time percentage)
— Input: timingConstraintID of type String - Handle to a timingConstraint element

### F.7.34 Constraint (EXTENDED)

#### F.7.34.1 removeConstraintSetDriveConstraint

Description: Removes the given driveConstraint.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: constraintSetID of type String - Handle to a constraintSet element

#### F.7.34.2 removeConstraintSetLoadConstraint

Description: Removes the given loadConstraint.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: constraintSetID of type String - Handle to a constraintSet element

#### F.7.34.3 removeConstraintSetTimingConstraint

Description: Removes the given timingConstraint.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: timingConstraintID of type String - Handle to a timingConstraint element

#### F.7.34.4 removeConstraintSetVector

Description: Removes vector from the given constraintSet.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: constraintSetID of type String - Handle to a constraintSet element

#### F.7.34.5 removeLoadConstraintCount

Description: Removes the given driveConstraint element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: loadConstraintID of type String - Handle to a loadConstraint element

#### F.7.34.6 setCellSpecificationCellClass

Description: Sets the cellClass value of the CellSpecification element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: cellSpecificationID of type String - Handle to a cellSpecification element
— Input: cellClass of type String - Enumerated value. Can be one of: combinational or sequential

#### F.7.34.7 setCellSpecificationCellFunction

Description: Sets the cellFunction value of the CellSpecification element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: cellSpecificationID of type String - Handle to a cellSpecification element
— Input: cellFunction of type String - Enumerated value. Can be of of: nand2, buf, inv, mux21,

dff, latch, xor2, or other

#### F.7.34.8 setConstraintSetDriveConstraint

Description: Sets a new driveConstraint with the given type to the given constraintSet.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: constraintSetID of type String - Handle to a constraintSet element
— Input: cellFunctionOrCellClass of type String - The driveConstraint type. Can be : nand2,

buf, inv, mux21, dff, latch, xor2, other, combinational or sequential

#### F.7.34.9 setConstraintSetLoadConstraint

Description: Adds a new loadConstraint with the given type to the given constraintSet.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: constraintSetID of type String - Handle to a constraintSet element
— Input: cellFuntionOrCellClass of type String - The loadConstraint type

#### F.7.34.10 setConstraintSetReferenceName

Description: Sets the given referenceName for the constraintSetId attribute for the given constraint set.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: constraintSetID of type String - Handle to a constraintSet element
— Input: referenceName of type String - The constraintSetId attribute value

#### F.7.34.11 setConstraintSetVector

Description: Sets the constraintSet vector left and right values.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: constraintSetID of type String - Handle to a constraintSet element
— Input: vector of type String[] - Vector left expression and right expression

#### F.7.34.12 setDriveConstraintOtherValue

Description: Sets the other attribute value for the given driveConstraint (cellFunction only).

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: driveConstraintID of type String - Handle to a driveConstraint element
— Input: other of type String - Value of the other attribute

#### F.7.34.13 setDriveConstraintValue

Description: Sets the given value for the given driveConstraint element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: driveConstraintID of type String - Handle to a driveConstraint element
— Input: value of type String - The driveConstraint value

#### F.7.34.14 setLoadConstraintCellSpecification

Description: Sets the cellSpecification on the given loadConstraint element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: loadConstraintID of type String - Handle to a loadConstraintElement
— Input: cellFunctionOrCellClass of type String - Define the type of the cellSpecification

depending on the value

#### F.7.34.15 setLoadConstraintCount

Description: Sets the given count for the given loadConstraint element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: loadConstraintID of type String - Handle to a loadConstraint element
— Input: count of type String - The loadConstraint count

#### F.7.34.16 setLoadConstraintOtherValue

Description: Sets the other attribute value for the given loadConstraint (cellFunction only).

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: loadConstraintID of type String - Handle to a loadConstraint element
— Input: other of type String - Value of the other attribute

#### F.7.34.17 setTimingConstraintValue

Description: Sets the given value for the given timingConstraint.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: timingConstraintID of type String - Handle to a timingConstraint element
— Input: value of type String - timingConstraint value

### F.7.35 Constraint Set (BASE)

#### F.7.35.1 getConstraintSetTimingConstraints

Description: Returns all the timingConstraint values defined on the given constraintSet element.

— Returns: timingConstraintValues of type Float - List of timingConstraint values
— Input: constraintSetID of type String - Handle to a constraintSet element

### F.7.36 Constraint Set (EXTENDED)

#### F.7.36.1 addConstraintSetTimingConstraint

Description: Adds a timingConstraint on the given constraintSet element

— Returns: timingConstraintId of type String - Handle to a timingConstraint element
— Input: constraintSetID of type String - Handle to a constraintSet element
— Input: value of type Float - The timingConstraint value
— Input: clockName of type String - The clockName value

### F.7.37 Design (BASE)

#### F.7.37.1 getActiveinterfaceExcludePortIDs

Description: Returns the handles to all the excludePorts defined on the given activeInterface element.

— Returns: excludePortID of type String - List of handles to the excludePort elements
— Input: activeInterfaceID of type String - Handle to an activeInterface element

#### F.7.37.2 getAdHocConnectionExternalPortReferenceIDs

Description: Returns the handles to all the externalPortReferences defined on the given adHocConnection
element.

— Returns: exernalPortReferenceIDs of type String - List of handles to

externalPortReference elements

— Input: adHocConnectionID of type String - Handle to an adHocConnection element

#### F.7.37.3 getAdHocConnectionInternalPortReferenceIDs

Description: Returns the handles to all the internalPortReferences defined on the given adHocConnection
element.

— Returns: internalPortReferenceIDs of type String - List of handles to

internalPortReference elements

— Input: adHocConnectionID of type String - Handle to an adHocConnection element

#### F.7.37.4 getAdHocConnectionTiedValue

Description: Returns tiedValue for the given adHocConnection element.

— Returns: value of type String - AdHoc connection tied value
— Input: adHocConnectionID of type String - Handle to an adHocConnection element

#### F.7.37.5 getAdHocConnectionTiedValueExpression

Description: Returns the tiedValue expression defined on the given adHocConnection element.

— Returns: valueExpression of type String - The tiedValue expression
— Input: adHocConnectionID of type String - Handle to an adHocConnection element

#### F.7.37.6 getAdHocConnectionTiedValueID

Description: Returns the handle to the tiedValue defined on the given adHocConnection element.

— Returns: tiedValueID of type String - Handle to the tiedValue element
— Input: adHocConnectionID of type String - Handle to an adHocConnection element

#### F.7.37.7 getInternalPortReferenceComponentInstanceRefByName

Description: Returns the componentInstanceRef defined on the given internalPortReference element.

— Returns: componentInstanceRef of type String - The referenced componentInstance name
— Input: internalPortReferenceID of type String - Handle to an internalPortReference element

#### F.7.37.8 getComponentInstanceComponentRefByID

Description: Returns the handle to the componentreferenced from the given componentInstance element.

— Returns: componentID of type String - Handle to the referenced component object
— Input: componentInstanceID of type String - Handle to a componentInstantiation element

#### F.7.37.9 getComponentInstanceComponentRefByVLNV

Description: Returns the VLNV of the component referenced from the given componentInstance element.

— Returns: VLNV of type String - The VLNV of the referenced component object
— Input: componentInstanceID of type String - Handle to a componentInstantiation element

#### F.7.37.10 getComponentInstanceName

Description: Returns the name of the given componentInstance element.

— Returns: name of type String - The componentInstance name
— Input: componentInstanceID of type String - Handle to a componentInstance element

#### F.7.37.11 getComponentInstancePowerDomainLinkIDs

Description: Returns the handles to all the powerDomainLinks defined on the given componentInstance
element.

— Returns: powerDomainLinkIDs of type String - List of handles to the powerDomainLink elements

— Input: componentInstanceID of type String - Handle to a componentInstance

#### F.7.37.12 getDesignAdHocConnectionIDs

Description: Returns the handles to all the adHocConnections defined on the given design object.

— Returns: adHocConnectionIDs of type String - List of handles to adHocConnection elements
— Input: designID of type String - Handle to a design object

#### F.7.37.13 getDesignChoiceIDs

Description: Returns the handles to all the choices defined on the given design object element.

— Returns: choiceIDs of type String - List of handles to choice elements
— Input: designID of type String - Handle to a design object element

#### F.7.37.14 getDesignComponentInstanceIDs

Description: Returns the handles to all the componentInstances defined on the given design object.

— Returns: componentInstanceIDs of type String - List of handles to componentInstance elements

— Input: designID of type String - Handle to a design object

#### F.7.37.15 getDesignID

Description: Returns the handle to the current or top design object associated with the currently invoked
generator.

— Returns: designID of type String - Handle to current or top design object
— Input: top of type Boolean - Indicates if the call must return top (true) or current (false) designID

#### F.7.37.16 getDesignInterconnectionIDs

Description: Returns the handles to all the interconnections defined on the given design object.

— Returns: interconnectionIDs of type String - List of handles to interconnection elements
— Input: designID of type String - Handle to a design object

#### F.7.37.17 getDesignMonitorInterconnectionIDs

Description: Returns the handles to all the monitorInterconnections defined on the given design object.

— Returns: monitorInterconnectionIDs of type String - List of handles to

monitorInterconnection elements

— Input: designID of type String - Handle to a design object

#### F.7.37.18 getExternalPortReferencePartSelectID

Description: Returns the handle to the partSelect element defined on the given externalPortReference
element.

— Returns: partSelectID of type String - Handle to the partSelect element
— Input: externalPortReferenceID of type String - Handle to an externalPortReference element

#### F.7.37.19 getExternalPortReferencePortRefByName

Description: Returns the portRef expression from an externalPortReference element.

— Returns: portRef of type String - The portRef expression
— Input: externalPortReferenceID of type String - The externalPortRefenreceID

#### F.7.37.20 getExternalPortReferenceSubPortReferenceIDs

Description: Returns the handles to all the subPortReferences defined on the given externalPortReference
element.

— Returns: subPortReferenceIDs of type String - List of handles to the subPortReference elements
— Input: externalPortReferenceID of type String - Handle to an externalPortReference element

#### F.7.37.21 getInterconnectionActiveInterfaceIDs

Description: Returns the handles to all the activeInterfaces defined on the given interconnection element.

— Returns: activeInterfaceIDs of type String - List of handles to activeInterface element
— Input: interconnectionID of type String - Handle to an interconnection element

#### F.7.37.22 getInterconnectionHierInterfaceIDs

Description: Returns the handles to all the hierInterfaces defined on the given activeInterface element.

— Returns: hierInterfaceIDs of type String - List of handles to hierInterface elements
— Input: interconnectionID of type String - Handle to an interconnection element

#### F.7.37.23 getInternalPortReferencePartSelectID

Description: Returns the handle to the partSelect element defined on the given internalPortReference
element.

— Returns: partSelectID of type String - Handle to the partSelect element
— Input: internalPortReferenceID of type String - Handle to an internalPortReference element

#### F.7.37.24 getInternalPortReferencePortRefByName

Description: Returns the portRef defined on the given internalPortReference element.

— Returns: portRef of type String - The referenced port name
— Input: internalPortReferenceID of type String - Handle to an internalPortReference element

#### F.7.37.25 getInternalPortReferenceSubPortReferenceIDs

Description: Returns the handles to all the subPortReferences defined on the given internalPortReference
element.

— Returns: subPortReferenceIDs of type String - List of handles to the subPortReference elements

— Input: internalPortReferenceID of type String - Handle to an internalPortReference element

#### F.7.37.26 getMonitorInterconnectionMonitorInterfaceIDs

Description: Returns the handles to all the monitorInterfaces defined on the given monitorInterconnection
element.

— Returns: monitorInterfaceIDs of type String - List of handles to the monitorInterface elements

— Input: monitorInterconnectionID of type String - Handle to a monitorInterconnection element

#### F.7.37.27 getMonitorInterconnectionMonitoredActiveInterfaceID

Description: Returns monitorActiveInterfaceID for the given monitorInterconnection element.

— Returns: monitoredInterfaceID of type String - Handle to a monitoredInterface
— Input: monitorInterconnectionID of type String - Handle to a monitorInterconnection element

#### F.7.37.28 getPowerDomainLinkExternalPowerDomainRef

Description: Returns the external power domain value from the given powerDomain link.

— Returns: externalRef of type String - The external power domain value
— Input: powerDomainLinkID of type String - Handle to a powerDomainLink element

#### F.7.37.29 getPowerDomainLinkExternalPowerDomainRefByID

Description: Returns the handle to the power domain referenced by the external reference from the given
powerDomainLink element.

— Returns: powerDomainID of type String - Handle to the power domain
— Input: powerDomainLinkID of type String - Handle to a powerDomainLink element

#### F.7.37.30 getPowerDomainLinkExternalPowerDomainRefByName

Description: Returns the external power domain referenced from the given powerDomainLink element.

— Returns: externalRef of type String - The referenced external power domain
— Input: powerDomainLinkID of type String - Handle to a powerDomainLink element

#### F.7.37.31 getPowerDomainLinkExternalPowerDomainRefExpression

Description: Returns the external power domain expression from the given powerDomain link.

— Returns: externalRef of type String - The external power domain expression
— Input: powerDomainLinkID of type String - Handle to a powerDomainLink element

#### F.7.37.32 getPowerDomainLinkExternalPowerDomainRefID

Description: Returns the handle to the external power domain from the given powerDomain link.

— Returns: expressionID of type String - Handle to the external power domain element
— Input: powerDomainLinkID of type String - Handle to a powerDomainLink element

#### F.7.37.33 getPowerDomainLinkInternalPowerDomainRefs

Description: Returns all the internal power domains referenced from the given powerDomainLink element.

— Returns: internalRef of type String - List of the referenced internal power domains
— Input: powerDomainLinkID of type String - Handle to a powerDomainLink element

### F.7.38 Design (EXTENDED)

#### F.7.38.1 addActiveInterfaceExcludePort

Description: add an excludePort on an active interface element

— Returns: excludePortID of type String - Handle to a new excludePort element
— Input: activeInterfaceID of type String - Handle to an active interface element
— Input: excludePort of type String - The excludePort name

#### F.7.38.2 addAdHocConnectionExternalPortReference

Description: Adds externalPortReference with the portRef to the given adHocConnection element.

— Returns: adHocExternalPortReferenceID of type String - Handle to an

externalPortReference element

— Input: adHocConnectionID of type String - Handle to an adHocConnection element
— Input: portRef of type String - Port name

#### F.7.38.3 addAdHocConnectionInternalPortReference

Description: Adds internalPortReference with the given componentInstanceRef and portRef to the given
adHocConnection element.

— Returns: adHocInternalPortReferenceID of type String - Handle to an

internalPortReference element

— Input: adHocConnectionID of type String - Handle to an adHocConnection element
— Input: componentInstanceRef of type String - Component instance name
— Input: portRef of type String - Port name

#### F.7.38.4 addDesignAdHocConnection

Description: Adds adHocConnection with the given name, componentInstanceRef, and portRef to the given
design element.

— Returns: adHocConnectionID of type String - Handle to an adHocConnection element
— Input: designID of type String - Handle to a design element
— Input: name of type String - AdHocConnection name
— Input: componentInstanceRef of type String - Component instance name
— Input: portRef of type String - Port name

#### F.7.38.5 addDesignChoice

Description: Adds a choice with the given name and enumerations to the given design element.

— Returns: choiceID of type String - Handle to a new choice
— Input: designID of type String - Handle to a design element
— Input: name of type String - Choice name
— Input: enumerations of type String[] - List of enumeration values

#### F.7.38.6 addDesignComponentInstance

Description: Adds componentInstance with the given VLNV and instance name to the given design element.

— Returns: componentInstanceID of type String - Handle to a component instance element
— Input: designID of type String - Handle to a design element
— Input: componentVLNV of type String[] - Component VLNV
— Input: componentInstanceName of type String - Component instance name

#### F.7.38.7 addDesignExternalAdHocConnection

Description: Adds adHocConnection with the given name and portRef to the given design element.

— Returns: adHocConnectionID of type String - Handle to an adHocConnection element
— Input: designID of type String - Handle to a design element
— Input: name of type String - AdHocConnection name
— Input: portRef of type String - Port name

#### F.7.38.8 addDesignInterconnection

Description: Adds interconnection with the given name between two component instance interfaces given
by ComponentInstanceRef1, busRef1, componentInstanceRef2, and busInterfaceRef2 to the given design
element.

— Returns: interconnectionID of type String - Handle to an interconnection element
— Input: designID of type String - Handle to a design element
— Input: name of type String - Interconnection name
— Input: componentInstanceRef1 of type String - Component instance name
— Input: busInterfaceRef1 of type String - Bus interface name
— Input: componentInstanceRef2 of type String - Component instance name
— Input: busInterfaceRef2 of type String - Bus interface name

#### F.7.38.9 addDesignMonitorInterconnection

Description: Adds monitorInterconnection with the given name, componentInstanceRef, and busRef to the
given design object.

— Returns: monitorInterconnectionID of type String - Handle to a monitorInterconnection element.

— Input: designID of type String - Handle to a design object
— Input: name of type String - MonitorInterconnection name
— Input: componentInstanceRef1 of type String - Component instance name
— Input: activeInterfaceBusInterfaceRef of type String - Bus interface name
— Input: componentInstanceRef2 of type String - Component instance name
— Input: interfaceBusInterfaceRef of type String - Bus interface name

#### F.7.38.10 addInterconnectionActiveInterface

Description: Adds activeInterface with the given componentInstanceRef and busRef to the given
interconnection element.

— Returns: activeInterfaceID of type String - Handle to an activeInterface element
— Input: interconnectionID of type String - Handle to an interconnection element
— Input: componentInstanceRef of type String - Component instance name
— Input: busInterfaceRef of type String - Bus interface name

#### F.7.38.11 addInterconnectionHierInterface

Description: Adds hierInterface with the given busRef to the given interconnection element.

— Returns: hierInterfaceID of type String - Handle to an hierInterface element
— Input: interconnectionID of type String - Handle to an interconnection element
— Input: busInterfaceRef of type String - Bus interface name

#### F.7.38.12 addMonitorInterconnectionMonitorInterface

Description: Adds monitorInterface with the given componentInstanceRef and busRef to the given
monitorInterconnection element.

— Returns: monitorInterfaceID of type String - Handle to a monitorInterface element
— Input: monitorInterconnectionID of type String - Handle to a monitorInterconnection element

— Input: componentInstanceRef of type String - Component instance name
— Input: busInterfaceRef of type String - Bus interface name

#### F.7.38.13 removeActiveInterfaceExcludePort

Description: Removes an excludePort on an active interface element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: excludePortID of type String - Handle to an excludePort element

#### F.7.38.14 removeAdHocConnectionExternalPortReference

Description: Removes the given externalPortReference element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: externalPortReferenceID of type String - Handle to an externalPortReference element

#### F.7.38.15 removeAdHocConnectionInternalPortReference

Description: Removes the given internalPortReference element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: internalPortReferenceID of type String - Handle to an internalPortReference element

#### F.7.38.16 removeAdHocConnectionTiedValue

Description: Removes tiedValue from the given adHocConnection element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: adHocConnectionID of type String - Handle to an adHocConnection element

#### F.7.38.17 removeDesignAdHocConnection

Description: Removes the given adHocConnection element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: adHocConnectionID of type String - Handle to an adHocConnection element

#### F.7.38.18 removeDesignChoice

Description: Removes the given choice element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: choiceID of type String - Handle to a choice element

#### F.7.38.19 removeDesignComponentInstance

Description: Removes the given componentInstance element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: componentInstanceID of type String - Handle to a componentInstance element

#### F.7.38.20 removeDesignInterconnection

Description: Removes the given interconnection element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: interconnectionID of type String - Handle to an interconnection element

#### F.7.38.21 removeDesignMonitorConnection

Description: Removes the given monitorInterconnection element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: monitorInterconnectionID of type String - Handle to a monitorInterconnection element

#### F.7.38.22 removeExternalPortReferencePartSelect

Description: Removes a partSelect on the given externalPort element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: externalPortReferenceID of type String - Handle to a portMap

externalPortReference element

#### F.7.38.23 removeExternalPortReferenceSubPortReference

Description: Removes the given subPort reference from the external PortReference of a structured port.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: subPortRefID of type String - Handle to an externalPortReference element

#### F.7.38.24 removeInterconnectionActiveInterface

Description: Removes the given activeInterface element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: activeInterfaceID of type String - Handle to an activeInterface element

#### F.7.38.25 removeInterconnectionHierInterface

Description: Removes the given hierInterface element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: hierInterfaceID of type String - Handle to an hierInterface element

#### F.7.38.26 removeInternalPortReferencePartSelect

Description: Removes a partSelect on the given internalPort element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: internalPortReferenceID of type String - Handle to a portMap internalPortReference element

#### F.7.38.27 removeInternalPortReferenceSubPortReference

Description: Removes the given subPort reference from the internalPortReference of a structured port.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: subPortRefID of type String - Handle to an subPortRef element

#### F.7.38.28 removeMonitorInterconnectionMonitorInterface

Description: Removes the given monitorInterface interface.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: monitorInterfaceID of type String - Handle to a monitorInterface element

#### F.7.38.29 setAdHocConnectionTiedValue

Description: Sets tiedValue with the given value for the given adHocConnection element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: adHocConnectionID of type String - Handle to an adHocConnection element
— Input: tiedValue of type String - AdHocConnection tied value

#### F.7.38.30 setComponentInstanceComponentRef

Description: Sets the componentRef with the given value for the given componentInstance element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: componentInstanceID of type String - Handle to an componentInstance element
— Input: componentVLNV of type String[] - component reference

#### F.7.38.31 setExternalPortReferencePartSelect

Description: Sets a partSelect on the given externalPort element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: externalPortReferenceID of type String - Handle to a portMap

externalPortReference element

— Input: range of type String[] - Create the range on the partSelect with “left” for range[0] and

“right” for range[1]. Set to null if you only want indices.

— Input: indices of type String[] - Handle to values of type String. Set all the index on the

partSelect

#### F.7.38.32 setInternalPortReferencePartSelect

Description: Sets a partSelect on the given internalPort element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: internalPortReferenceID of type String - Handle to a portMap internalPortReference element
— Input: range of type String[] - Create the range on the partSelect with “left” for range[0] and “right” for range[1]. Set to null if you only want indices.
— Input: indices of type String[] - Handle to values of type String. Set all the index on the partSelect

#### F.7.38.33 setInterconnectionActiveInterface

Description: Sets the active interface of an interconnection.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: interconnectionID of type String - Handle to interconnection
— Input: componentInstanceRef of type String - Component interface name
— Input: busRef of type String - Bus interface name

#### F.7.38.34 setInterconnectionHierInterface

Description: Sets the hierarchical interface of an interconnection.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: interconnectionID of type String - Handle to interconnection
— Input: busRef of type String - Bus interface name

#### F.7.38.35 setMonitorInterconnectionMonitoredActiveInterface

Description: Sets the monitoredActiveInterface on a monitorInterconnection element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: monitorInterconnectionID of type String - Handle to a monitorInterconnection element

— Input: componentInstanceRef of type String - The componentInstanceRef to be set
— Input: busRef of type String -The busRef attribute to be set

#### F.7.38.36 setMonitoredActiveInterfacePath

Description: Sets path with the given value for the given monitoredActiveInterface element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: monitoredActiveInterfaceID of type String - Handle to a monitoredActiveInterface element

— Input: path of type String - Hierarchical path separated by a slash

#### F.7.38.37 setPowerDomainLinkExternalPowerDomainRef

Description: Sets the external power domain reference to the expression by the given powerDomain link.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: powerDomainLinkID of type String - Handle to a powerDomainLink element
— Input: expression of type String - The new value or expression

### F.7.39 Design configuration (BASE)

#### F.7.39.1 getAbstractorInstanceAbstractorRefByID

Description: Returns the handle to the abstractor instance referenced from the given abstractorInstance
element.

— Returns: abstractorID of type String - Handle to the referenced abstractor object
— Input: abstractorInstanceID of type String - Handle to an abstractorInstance element


#### F.7.39.2 getAbstractorInstanceAbstractorRefByVLNV

Description: Returns the VLNV of the abstractor referenced from the given abstractorInstance element.

— Returns: VLNV of type String - The VLNV of the referenced abstractor object
— Input: abstractorInstanceID of type String - Handle to an abstractorInstance element

#### F.7.39.3 getAbstractorInstanceInstanceName

Description: Returns the instanceName defined on the given abstractorInstance element.

— Returns: instanceName of type String - The instance name
— Input: abstractorInstanceID of type String - Handle to an abstractorInstance element

#### F.7.39.4 getAbstractorInstanceViewName

Description: Returns viewName for the given abstractorInstance element.

— Returns: viewName of type String - Abstractor view name
— Input: abstractorInstanceID of type String - Handle to an abstractorInstance element

#### F.7.39.5 getAbstractorInstancesAbstractorInstanceIDs

Description: Returns the handles to all the abstractorInstances defined on the given abstractorInstances
element.

— Returns: abstractorInstanceIDs of type String - List of handles to abstractorInstance elements

— Input: abstractorInstancesID of type String - Handle to an abstractorInstances element

#### F.7.39.6 getAbstractorInstancesInterfaceRefIDs

Description: Returns the handles
abstractorInstances element.

to all

the abstractorInstancesInterfaces defined on the given

— Returns: abstractorInstancesInterfaceIDs of type String - List of handles to the

abstractorInstancesInterface elements

— Input: abstractorInstancesID of type String - Handle to an abstractorInstances element

#### F.7.39.7 getDesignConfigurationChoiceIDs

Description: Returns the handles to all the choices defined on the given designConfiguration element.

— Returns: choiceIDs of type String - List of handles to choice elements
— Input: designConfigurationID of type String - Handle to a designConfiguration element

#### F.7.39.8 getDesignConfigurationDesignRefByID

Description: Returns the handle to the design instance referenced in the given designConfiguration element.

— Returns: designID of type String - Handle to the referenced design object
— Input: designConfigurationID of type String - Handle to a designConfiguration element

#### F.7.39.9 getDesignConfigurationDesignRefByVLNV

Description: Returns the VLNV of the design referenced from the given designConfiguration element.

— Returns: VLNV of type String - The VLNV of the referenced design object
— Input: designConfigurationID of type String - Handle to a designConfiguration element

#### F.7.39.10 getDesignConfigurationGeneratorChainConfigurationIDs

Description: Returns the handles to all the generatorChainConfigurations defined on the given
designConfiguration object.

— Returns: generatorChainConfigurationIDs of type String - List of handles to

generatorChainConfiguration elements

— Input: designConfigurationID of type String - Handle to a designConfiguration object

#### F.7.39.11 getDesignConfigurationInterconnectionConfigurationIDs

Description: Returns the handles to all the interconnectionConfigurations defined on the given
designConfiguration object.

— Returns: interconnectionConfigurationIDs of type String - List of handles to

interconnectionConfiguration elements

— Input: designConfigurationOrDesignConfigurationInstanceID of type String -

Handle to a designConfiguration or designConfigurationInstance element

#### F.7.39.12 getDesignConfigurationViewConfigurationIDs

Description: Returns the handles to all the viewConfigurations defined on the given designConfiguration
object.

— Returns: viewConfigurationIDs of type String - List of handles to viewConfiguration elements

— Input: designConfigurationOrDesignConfigurationInstanceID of type String -

Handle to a designConfiguration or designConfigurationInstance element

#### F.7.39.13 getGeneratorChainConfigurationRefByID

Description: Returns
the handle
generatorChainConfiguration element.

to

the generatorChain

instance

referenced

from

the given

— Returns: generatorChainID of type String - Handle to the referenced generatorChain object
— Input: generatorChainConfigurationID of type String - Handle to a

generatorChainConfiguration element

#### F.7.39.14 getGeneratorChainConfigurationRefByVLNV

Description: Returns the VLNV of the generatorChainConfiguration referenced from the given
generatorChainConfiguration element.

— Returns: generatorChainConfigurationVLNV of type String - The VLNV of

generatorChainConfiguration

— Input: generatorChainConfigurationID of type String - Handle to a

generatorChainConfiguration element

#### F.7.39.15 getInterconnectionConfigurationAbstractorsInstancesIDs

Description: Returns the handles to all the abstractorInstances defined on the given interconnectionConfiguration element

— Returns: abstractorInstancesIDs of type String - List of handles to the abstractorInstances elements
— Input: interconnectionConfigurationID of type String - Handle to an

interconnectConfiguration element

#### F.7.39.16 getInterconnectionConfigurationInterconnectionRefByID

Description: Returns the handle to the interconnection referenced from the given interconnectionConfiguration element.

— Returns: interconnectionID of type String - Handle to the referenced interconnection
— Input: interconnectionConfigurationID of type String - Handle to an interconnectConfiguration element

#### F.7.39.17 getInterconnectionConfigurationInterconnectionRefByName

Description: Returns the interconnectionRef defined on the given interconnectionConfiguration element.

— Returns: interconnectionRef of type String - The referenced interconnection
— Input: interconnectionConfigurationID of type String - Handle to an

interconnectionConfiguration element

#### F.7.39.18 getViewConfigurationConfigurableElementValueIDs

Description: Returns
viewConfiguration element.

the handles

to all

the configurableElementValues defined on

the given

— Returns: configurableElementValueIDs of type String - List of handles to

configurableElementValue elements

— Input: viewConfigurationID of type String - Handle to a viewConfiguration element

#### F.7.39.19 getViewConfigurationInstanceName

Description: Returns instanceName for the given viewConfiguration element.

— Returns: instanceName of type String - Component instance name
— Input: viewConfigurationID of type String - Handle to a viewConfiguration element

#### F.7.39.20 getViewConfigurationViewID

Description: Returns the handle to the view defined on the given viewConfiguration element.

— Returns: viewID of type String - Handle to the view element
— Input: viewConfigurationID of type String - Handle to a viewConfiguration element

#### F.7.39.21 getViewConfigurationViewRefByName

Description: Returns the viewRef defined on the given viewConfiguration element.

— Returns: viewRef of type String - The referenced view
— Input: viewConfigurationID of type String - Handle to a view element

### F.7.40 Design configuration (EXTENDED)

#### F.7.40.1 addAbstractorInstancesAbstractorInstance

Description: Adds abstractorInstance with the given VLNV, instance, and viewName to the given
abstractorInstances element.

— Returns: abstractorInstanceID of type String - Handle to an abstractorInstantiations element
— Input: abstractorInstancesID of type String - Handle to an abstractorInstances element
— Input: abstractorVLNV of type String[] - Abstractor VLNV
— Input: instanceName of type String - Abstractor instance name
— Input: viewName of type String - Abstractor instance view name

#### F.7.40.2 addAbstractorInstancesInterfaceRef

Description: Adds abstractorInstancesInterface with the given componentRef and busRef to the given
abstractorInstances element.

— Returns: interfaceRef of type String - Handle to the new interfaceRef element
— Input: abstractorInstancesID of type String - Handle to an abstractorInstances element
— Input: componentInstanceName of type String - The componentInstance name
— Input: busRef of type String - BusInterface name

#### F.7.40.3 addDesignConfChoice

Description: Adds a choice with the given name and enumerations to the given design configuration
element.

— Returns: choiceID of type String - Handle to a new choice
— Input: designConfID of type String - Handle to a design configuration element
— Input: name of type String - Choice name
— Input: enumerations of type String[] - List of enumeration values

#### F.7.40.4 addDesignConfigurationGeneratorChainConfiguration

Description: Adds generatorChainConfiguration with the given VLNV to the given designConfiguration
element.

— Returns: generatorChainConfigurationID of type String - Handle to a

generatorChainConfiguration element

— Input: designConfigurationID of type String - Handle to a designConfiguration element
— Input: generatorVLNV of type String[] - Generator VLNV

#### F.7.40.5 addDesignConfigurationInterconnectionConfiguration

Description: Adds interconnectionConfiguration with the given interconnectionRef, VLNV, instance, and
viewName to the given designConfiguration element.

— Returns: interconnectionConfigurationID of type String - Handle to an

interconnectionConfiguration

— Input: designConfigurationID of type String - Handle to a designConfiguration element
— Input: interconnectionRef of type String - Interconnection name
— Input: abstractorVLNV of type String[] - Abstractor VLNV
— Input: instanceName of type String - Abstractor instance name
— Input: viewName of type String - Abstractor instance view name

#### F.7.40.6 addDesignConfigurationViewConfiguration

Description: Adds viewConfiguration with the given instanceName and viewName to the given
designConfiguration element.

— Returns: viewConfigurationID of type String - Handle to a viewConfiguration element
— Input: designConfigurationID of type String - Handle to a designConfiguration element
— Input: componentInstanceName of type String - ComponentInstance name
— Input: viewName of type String - Component view name

#### F.7.40.7 addInterconnectionConfigurationAbstractorInstances

Description: Adds abstractorInstances with the given VLNV, instance, and viewName to the given
interconnectionConfiguration element.

— Returns: abstractorInstancesID of type String - Handle to an abstractorInstances element
— Input: interconnectionConfigurationID of type String - Handle to an

interconnectConfiguration element

— Input: abstractorVLNV of type String[] - Abstractor VLNV
— Input: instanceName of type String - Abstractor instance name
— Input: viewName of type String - Abstractor instance view name

#### F.7.40.8 removeAbstractorInstancesAbstractorInstance

Description: Removes the given abstractorInstance element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractorInstancesID of type String - Handle to an abstractorInstances element

#### F.7.40.9 removeAbstractorInstancesInterfaceRef

Description: Removes the given abstractorInstancesInterface element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: interfaceRefID of type String - Handle to an interfaceRef element

#### F.7.40.10 removeDesignConfChoice

Description: Removes the given choice element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: choiceID of type String - Handle to a choice element

#### F.7.40.11 removeDesignConfigurationDesignRef

Description: Removes designRef from the given designConfiguration element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: designConfigurationID of type String - Handle to a designConfiguration element

#### F.7.40.12 removeDesignConfigurationGeneratorChainConfiguration

Description: Removes the given generatorChainConfiguration element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: generatorChainConfigurationID of type String - Handle to a

generatorChainConfigurationElement

#### F.7.40.13 removeDesignConfigurationInterconnectionConfiguration

Description: Removes the given interconnectionConfiguration element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: interconnectionConfigurationID of type String - Handle to an

interconnectConfiguration element

#### F.7.40.14 removeDesignConfigurationViewConfiguration

Description: Removes the given viewConfiguration element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: viewConfigurationID of type String - Handle to a viewConfiguration element

#### F.7.40.15 removeInterconnectionConfigurationAbstractorInstances

Description: Removes the given abstractorInstances element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractorInstancesID of type String - Handle to an abstractorInstances element

#### F.7.40.16 removeViewConfigurationConfigurableElementValue

Description: Removes the given configurable element value from its containing viewConfiguration element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: configurableElementValueID of type String - Handle to the

configurableElementValue

#### F.7.40.17 setAbstractorInstanceAbstractorRef

Description: Sets the abstractorRef on an abstractorInstance element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractorInstanceID of type String - Handle to an abstractorInstance element
— Input: vlnv of type String[] - The vlnv to be set on the abstractorRef

#### F.7.40.18 setAbstractorInstanceInstanceName

Description: Sets the instanceName on an abstractorInstance element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractorInstanceID of type String - Handle to an abstractorInstance element
— Input: instanceName of type String - The instanceName expression

#### F.7.40.19 setAbstractorInstanceViewName

Description: Sets the viewName on an abstractorInstance element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractorInstanceID of type String - Handle to an abstractorInstance element
— Input: viewName of type String - The viewname expression

#### F.7.40.20 setDesignConfigurationDesignRef

Description: Sets designRef with the given VLNV for the given designConfiguration element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: designConfigurationID of type String - Handle to a designConfiguration element
— Input: designVLNV of type String[] - Design VLNV

#### F.7.40.21 setInterconnectionConfigurationInterconnectionRef

Description: get the interonnectionRef on an interconnectionConfiguration element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: interconnectionConfigurationID of type String - Handle to an

interconnectionConfiguration element

— Input: interconnectionRef of type String - The interconnectionRef expression

#### F.7.40.22 setViewConfigurationInstanceName

Description: Sets the instanceName on a viewConfiguration element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: viewConfigurationID of type String - Handle to a viewConfiguration element
— Input: instanceName of type String - The instanceName expression

#### F.7.40.23 setViewConfigurationView

Description: Sets the view on a viewConfiguration element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: viewConfigurationID of type String - Handle to a viewConfiguration element
— Input: viewRef of type String - the viewRef expression

### F.7.41 Driver (BASE)

#### F.7.41.1 getClockDriverClockPeriod

Description: Returns the clockPeriod defined on the given clockDriver element.

— Returns: clockPeriod of type Double - The clock period value
— Input: clockDriverID of type String - Handle to a clockDriver element

#### F.7.41.2 getClockDriverClockPeriodExpression

Description: Returns the clockPeriod expression defined on the given clockDriver element.

— Returns: clockPeriodExpression of type String - The clockPeriod expression
— Input: clockDriverID of type String - Handle to a clockDriver element

#### F.7.41.3 getClockDriverClockPeriodID

Description: Returns the handle to the clockPeriod defined on the given clockDriver element.

— Returns: clockPeriodID of type String - Handle to the clockPeriod element
— Input: clockDriverID of type String - Handle to a clockDriver element

#### F.7.41.4 getClockDriverClockPulseDuration

Description: Returns the clockPulseDuration defined on the given clockDriver element.

— Returns: clockPulseDuration of type Double - The clock pulse duration value
— Input: clockDriverID of type String - Handle to a clockDriver element

#### F.7.41.5 getClockDriverClockPulseDurationExpression

Description: Returns the clockPulseDuration expression defined on the given clockDriver element.

— Returns: clockPulseDurationExpression of type String - The clockPulseDuration

expression

— Input: clockDriverID of type String - Handle to a clockDriver element

#### F.7.41.6 getClockDriverClockPulseDurationID

Description: Returns the handle to the pulseDuration defined on the given clockDriver element.

— Returns: pulseDurationID of type String - Handle to the pulseDuration element
— Input: clockDriverID of type String - Handle to a clockDriver element

#### F.7.41.7 getClockDriverClockPulseOffset

Description: Returns the clockPulseOffset defined on the given clockDriver element.

— Returns: clockPulseOffset of type Double - The clock pulse offset value
— Input: clockDriverID of type String - Handle to a clockDriver element

#### F.7.41.8 getClockDriverClockPulseOffsetExpression

Description: Returns the clockPulseOffset expression defined on the given clockDriver element.

— Returns: clockPulseOffsetExpression of type String - The clockPulseOffset expression
— Input: clockDriverID of type String - Handle to a clockDriver element

#### F.7.41.9 getClockDriverClockPulseOffsetID

Description: Returns the handle to the pulseOffset defined on the given clockDriver element.

— Returns: pulseOffsetID of type String - Handle to the pulseOffset element
— Input: clockDriverID of type String - Handle to a clockDriver element

#### F.7.41.10 getClockDriverClockPulseValue

Description: Returns the clockPulseValue defined on the given clockDriver element.

— Returns: clockPulseValue of type Boolean - The clock pulse value
— Input: clockDriverID of type String - Handle to a clockDriver element

#### F.7.41.11 getClockDriverClockPulseValueExpression

Description: Returns the clockPulseValue expression defined on the given clockDriver element.

— Returns: clockPulseValueExpression of type String - The clockPulseValue expression
— Input: clockDriverID of type String - Handle to a clockDriver element

#### F.7.41.12 getClockDriverClockPulseValueID

Description: Returns the handle to the pulseValue defined on the given clockDriver element.

— Returns: pulseValueID of type String - Handle to the pulseValue element
— Input: clockDriverID of type String - Handle to a clockDriver element

#### F.7.41.13 getDriverClockDriverID

Description: Returns the handle to the clockDriver defined on the given driver element.

— Returns: clockDriverID of type String - Handle to the clockDriver
— Input: driverID of type String - Handle to a driver element

#### F.7.41.14 getDriverDefaultValue

Description: Returns the default value defined on the given driver element.

— Returns: defaultValue of type String - The driver default value
— Input: driverID of type String - Handle to a driver element

#### F.7.41.15 getDriverDefaultValueExpression

Description: Returns the defaultValue expression defined on the given driver element.

— Returns: defaultValueExpression of type String - The defaultValue expression
— Input: driverID of type String - Handle to a driver element

#### F.7.41.16 getDriverDefaultValueID

Description: Returns the handle to the defaultValue defined on the given driver element.

— Returns: defaultValueID of type String - Handle to the defaultValue element
— Input: driverID of type String - Handle to a driver element

#### F.7.41.17 getDriverLeftID

Description: Returns the handle to the left range defined the given driver element.

— Returns: leftID of type String - Handle to the left range element
— Input: driverID of type String - Handle to a driver element

#### F.7.41.18 getDriverRange

Description: Returns the range left and right (resolved) values defined on the given driver element.

— Returns: rangeValues of type Long - Array of two range values: left and right
— Input: driverID of type String - Handle to a driver element

#### F.7.41.19 getDriverRangeExpression

Description: Returns the range left and right expressions defined on the given driver element.

— Returns: rangeExpressions of type String - Array of two range expressions: left and right
— Input: driverID of type String - Handle to a driver element

#### F.7.41.20 getDriverRightID

Description: Returns the handle to the right range defined the given driver element.

— Returns: rightID of type String - Handle to the right range element
— Input: driverID of type String - Handle to a driver element

#### F.7.41.21 getDriverSingleShotDriverID

Description: Returns the handle to the singleShotDriver element defined on the given driver element.

— Returns: singleShotDriverID of type String - Handle to the singleShotDriver element
— Input: driverID of type String - Handle to a driver element

#### F.7.41.22 getDriverViewRefByID

Description: Returns the handle to the view defined on the driver element.

— Returns: viewID of type String - Handles to a view element
— Input: driverID of type String - Handle to a driver element
— Input: viewRef of type String - Handle to the viewRef element

#### F.7.41.23 getDriverViewRefIDs

Description: Returns the handles to all the viewRefs defined on the driver element.

— Returns: viewRefIDs of type String - List of handles to the viewRef elements
— Input: driverID of type String - Handle to a driver element

#### F.7.41.24 getOtherClockDriverClockPeriod

Description: Returns the clockPeriod value defined on the given otherClockDriver element.

— Returns: clockPeriod of type Double - The clockPeriod value
— Input: otherClockDriverID of type String - Handle to an otherClockDriver element

#### F.7.41.25 getOtherClockDriverClockPeriodExpression

Description: Returns the clockPeriod expression defined on the given otherClockDriver element.

— Returns: clockPeriod of type String - The clockPeriod expression
— Input: otherClockDriverID of type String - Handle to an otherClockDriver element

#### F.7.41.26 getOtherClockDriverClockPeriodID

Description: Returns the handle to the clockPeriod defined on the given otherClockDriver element.

— Returns: clockPeriodID of type String - Handle to the clockPeriod element
— Input: otherClockDriverID of type String - Handle to an otherClockDriver element

#### F.7.41.27 getOtherClockDriverClockPulseDuration

Description: Returns the clockPulseDuration value defined on the given otherClockDriver element.

— Returns: clockPulseDuration of type Double - The clockPulseDuration value
— Input: otherClockDriverID of type String - Handle to an otherClockDriver element

#### F.7.41.28 getOtherClockDriverClockPulseDurationExpression

Description: Returns the clockPulseDuration expression defined on the given otherClockDriver element.

— Returns: clockPulseDurationExpression of type String - The clockPulseDuration

expression

— Input: otherClockDriverID of type String - Handle to an otherClockDriver element

#### F.7.41.29 getOtherClockDriverClockPulseDurationID

Description: Returns the handle to the clockPulseDuration defined on the given otherClockDriver element.

— Returns: clockPulseDurationID of type String - Handle to the clockPulseDuration element
— Input: otherClockDriverID of type String - Handle to an otherClockDriver element

#### F.7.41.30 getOtherClockDriverClockPulseOffset

Description: Returns the clockPulseOffset value defined on the given otherClockDriver element.

— Returns: clockPulseOffset of type Double - The clockPulseOffset value
— Input: otherClockDriverID of type String - Handle to a otherClockDriver element

#### F.7.41.31 getOtherClockDriverClockPulseOffsetExpression

Description: Returns the clockPulseOffset expression defined on the given otherClockDriver element.

— Returns: clockPulseOffsetExpression of type String - The clockPulseOffset expression
— Input: otherClockDriverID of type String - Handle to an otherClockDriver element

#### F.7.41.32 getOtherClockDriverClockPulseOffsetID

Description: Returns the handle to the clockPulseOffset defined on the given otherClockDriver element.

— Returns: clockPulseOffsetID of type String - Handle to the clockPulseOffset element
— Input: otherClockDriverID of type String - Handle to an otherClockDriver element

#### F.7.41.33 getOtherClockDriverClockPulseValue

Description: Returns the clockPulseValue value defined on the given otherClockDriver element.

— Returns: clockPulseValue of type Boolean - The clockPulseValue value
— Input: otherClockDriverID of type String - Handle to an otherClockDriver element

#### F.7.41.34 getOtherClockDriverClockPulseValueExpression

Description: Returns the clockPulseValue expression defined on the given otherClockDriver element.

— Returns: clockPulseValueExpression of type String - The clockPulseValue expression
— Input: otherClockDriverID of type String - Handle to an otherClockDriver element

#### F.7.41.35 getOtherClockDriverClockPulseValueID

Description: Returns the handle to the clockPulseValue defined on the given otherClockDriver element.

— Returns: clockPulseValueID of type String - Handle to the clockPulseValue element
— Input: otherClockDriverID of type String - Handle to an otherClockDriver element

#### F.7.41.36 getSingleShotDriverSingleShotDuration

Description: Returns the singleShotDuration defined on the given singleShotDriver element.

— Returns: singleShotDuration of type Double - The single shot duration
— Input: singleShotDriverID of type String - Handle to a singleShotDriver element

#### F.7.41.37 getSingleShotDriverSingleShotDurationExpression

Description: Returns the singleShotDuration expression defined on the given singleShotDriver element.

— Returns: singleShotDurationExpression of type String - The singleShotDuration

expression

— Input: singleShotDriverID of type String - Handle to a singleShotDriver element

#### F.7.41.38 getSingleShotDriverSingleShotDurationID

Description: Returns the handle to the singleShotDuration element defined on the given singleShotDriver
element.

— Returns: singleShotDurationID of type String - Handle to the singleShotDuration element
— Input: singleShotDriverID of type String - Handle to a singleShotDriver element

#### F.7.41.39 getSingleShotDriverSingleShotOffset

Description: Returns the singleShotOffset defined on the given singleShotDriver element.

— Returns: singleShotOffset of type Double - The single shot offset value
— Input: singleShotDriverID of type String - Handle to a singleShotDriver element

#### F.7.41.40 getSingleShotDriverSingleShotOffsetExpression

Description: Returns the singleShotOffset expression defined on the given singleShotDriver element.

— Returns: singleShotOffsetExpression of type String - The singleShotOffset expression
— Input: singleShotDriverID of type String - Handle to a singleShotDriver element

#### F.7.41.41 getSingleShotDriverSingleShotOffsetID

Description: Returns the handle to singleShotOffset element defined on the given singleShotDriver element.

— Returns: singleShotOffsetID of type String - Handle to the singleShotOffset element
— Input: singleShotDriverID of type String - Handle to a singleShotDriver element

#### F.7.41.42 getSingleShotDriverSingleShotValue

Description: Returns the singleShotValue defined on the given singleShotDriver element.

— Returns: singleShotValue of type Long - The single shot value
— Input: singleShotDriverID of type String - Handle to a singleShotDriver element

#### F.7.41.43 getSingleShotDriverSingleShotValueExpression

Description: Returns the singleShotValue expression defined on the given singleShotDriver element.

— Returns: singleShotValueExpression of type String - The singleShotValue expression
— Input: singleShotDriverID of type String - Handle to a singleShotDriver element

#### F.7.41.44 getSingleShotDriverSingleShotValueID

Description: Returns the handle to the singleShotValue element defined on the given singleShotDriver
element.

— Returns: singleShotValueID of type String - Handle to the singleShotValue element
— Input: singleShotDriverID of type String - Handle to a singleShotDriver element

### F.7.42 Driver (EXTENDED)

#### F.7.42.1 addDriverSingleShotDriver

Description: Adds a single shot driver with the given details to the given driver element.

— Returns: singleShotDriverID of type String - Handle to a new singleShotDriver
— Input: driverID of type String - Handle to a driver element
— Input: offset of type String - Single shot offset expression
— Input: value of type String - Single shot value expression
— Input: duration of type String - Single shot duration expression

#### F.7.42.2 addDriverViewRef

Description: Adds a reference to a view name in the file for which this type applies.

— Returns: viewRefID of type String - Handle to the added viewRef
— Input: driverID of type String - Handle to a driver element
— Input: viewRef of type String - Referenced view name

#### F.7.42.3 removeDriverClockDriver

Description: Removes the clock driver from the given driver element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: driverID of type String - Handle to a driver element

#### F.7.42.4 removeDriverRange

Description: Removes the range from the given driver.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: driverID of type String - Handle to a driver element

#### F.7.42.5 removeDriverSingleShotDriver

Description: Removes the single shot driver from the given driver element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: driverID of type String - Handle to a driver element

#### F.7.42.6 removeDriverViewRef

Description: Removes the given viewRef from its containing Driver element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: viewRefID of type String - Handle to a viewRef element

#### F.7.42.7 setClockDriverClockPeriod

Description: Sets the clockPeriod on the given clockDriver element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: clockDriverID of type String - Handle to a clockDriver element
— Input: clockPeriod of type String - The clockPeriod expression

#### F.7.42.8 setClockDriverClockPulseDuration

Description: Sets the clockPulseDuration on the given clockDriver element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: clockDriverID of type String - Handle to a clockDriver element
— Input: clockPulseDuration of type String - The clockPulseDuration expression

#### F.7.42.9 setClockDriverClockPulseOffset

Description: Sets the pulseOffset on the given clockDriver element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: clockDriverID of type String - Handle to a clockDriver element
— Input: pulseOffset of type String - The pulseOffset expression

#### F.7.42.10 setClockDriverClockPulseValue

Description: Sets the clockPulseValue on the given clockDriver element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: clockDriverID of type String - Handle to a clockDriver element
— Input: clockPulseValue of type String - The clockPulseValue expression

#### F.7.42.11 setDriverClockDriver

Description: Sets the clockDriver on the given driver element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: driverID of type String - Handle to a driver element
— Input: clockPeriod of type String - The clockPeriod expression
— Input: clockPulseOffset of type String - The clockPulseOffset expression
— Input: clockPulseValue of type String - The clockPulseValue expression
— Input: clockPulseDuration of type String - The clockPulseDuration expression

#### F.7.42.12 setDriverSingleShotDriver

Description: Sets the singleShotDriver on the given driver element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: driverID of type String - Handle to a driver element
— Input: singleShotOffset of type String - The singleShotOffset expression
— Input: singleShotValue of type String - The singleShotValue expression
— Input: singleShotDuration of type String - The singleShotDuration expression

#### F.7.42.13 setDriverDefaultValue

Description: Sets a Default value for a wire port.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: driverID of type String - Handle to a driver element
— Input: value of type String - Default driver value

#### F.7.42.14 setDriverRange

Description: Sets the range of the given driver.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: driverID of type String - Handle to a driver element
— Input: range of type String[] - Range with left at index 0 and right at index 1

#### F.7.42.15 setOtherClockDriverClockPeriod

Description: Sets a clockPeriod element on an otherClockDriver element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: otherClockDriverID of type String - Handle to an otherClockDriver element
— Input: clockPeriod of type String - Clock period value

#### F.7.42.16 setOtherClockDriverClockPulseDuration

Description: Sets a clockPulseDuration element on an otherClockDriver element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: otherClockDriverID of type String - Handle to an otherClockDriver element
— Input: clockPulseDuration of type String - Clock pulse offset value

#### F.7.42.17 setOtherClockDriverClockPulseOffset

Description: Sets a clockPulseOffset element on an otherClockDriver element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: otherClockDriverID of type String - Handle to an otherClockDriver element
— Input: clockPulseOffset of type String - Clock pulse offset value

#### F.7.42.18 setOtherClockDriverClockPulseValue

Description: Sets a clockPulseValue element on an otherClockDriver element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: otherClockDriverID of type String - Handle to an otherClockDriver element
— Input: clockPulseValue of type String - Clock pulse offset value

#### F.7.42.19 setSingleShotDriverSingleShotDuration

Description: Sets the singleShotDuration on the given singleShotDriver element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: singleShotDriverID of type String - Handle to a singleShotDuration element
— Input: singleShotDuration of type String - The singleShotDuration expression

#### F.7.42.20 setSingleShotDriverSingleShotOffset

Description: Sets the singleShotOffset on the given singleShotDriver element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: singleShotDriverID of type String - Handle to a singleShotDriver element
— Input: singleShotOffset of type String - The singleShotOffset expression

#### F.7.42.21 setSingleShotDriverSingleShotValue

Description: Sets the singleShotValue on the given singleShotDriver element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: singleShotDriverID of type String - Handle to a singleShotDriver element
— Input: singleShotValue of type String - The singleShotValue expression

### F.7.43 Element attribute (BASE)

#### F.7.43.1 getAddressBlockRefAttribute

Description: Returns the attribute “addressBlockRef” defined on the given addressBlockRef element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.2 getAddressBlockRefAttributeByID

Description: Returns the handle to the addressBlock referenced from the given element.

— Returns: addressBlockID of type String - Handle to the referenced addressBlock
— Input: addressBlockRefID of type String - Handle to an element

#### F.7.43.3 getAddressSpaceRefAttribute

Description: Returns the attribute “addressSpaceRef” defined on the given element

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.4 getAddressSpaceRefAttributeByID

Description: Returns the handle to the addressSpace referenced from the attribute of the given element.

— Returns: addressSpaceID of type String - Handle to the referenced addressSpace
— Input: elementID of type String - Handle to an element

#### F.7.43.5 getAllBitsBooleanAttribute

Description: Returns the attribute “allBits” defined on the given wirePort width element.

— Returns: attributeValue of type Boolean - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.6 getAllLogicalDirectionsAllowedBooleanAttribute

Description: Returns the attribute “allLogicalDirectionsAllowed” defined on the given element.

— Returns: attributeValue of type Boolean - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.7 getAllLogicalInitiativesAllowedBooleanAttribute

Description: Returns the attribute “allLogicalInitiativesAllowed” defined on the given element.

— Returns: attributeValue of type Boolean - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.8 getAlternateRegisterRefAttribute

Description: Returns the attribute “alternateRegisterRef” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.9 getAlternateRegisterRefAttributeByID

Description: Returns the handle to the alternateRegister referenced from the given alternateRegisterRef
element.

— Returns: alternateRegisterID of type String - Handle to the referenced alternateRegister element

— Input: alternateRegisterRefID of type String - Handle to an alternateRegisterRef element

#### F.7.43.10 getAppendBooleanAttribute

Description: Returns the attribute “append” defined on the given file buildCommand flags element.

— Returns: attributeValue of type Boolean - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.11 getArrayIdAttribute

Description: Returns the attribute “arrayId” of the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.12 getBankAlignmentAttribute

Description: Returns the attribute “bankAlignment” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.13 getBankRefAttribute

Description: Returns the attribute “bankRef” defined on the given memoryMapRef element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.14 getBankRefAttributeByID

Description: Returns the handle to the bank referenced from the given bankRef element.

— Returns: bankID of type String - Handle to the referenced bank element
— Input: bankRefID of type String - Handle to a bankRef element

#### F.7.43.15 getBusRefAttribute

Description: Returns the attribute “busRef” defined on the given element

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.16 getBusRefAttributeByID

Description: Returns the handle to the busInterface defined on the given element.

— Returns: busInterfaceID of type String - Handle to the referenced busInterface
— Input: elementID of type String - Handle to an element

#### F.7.43.17 getCellStrengthAttribute

Description: Returns the attribute “cellStrength” defined on the given cellSpecification element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.18 getChoiceRefAttribute

Description: Returns the attribute “choiceRef” defined on the given parameter element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.19 getChoiceRefAttributeByID

Description: Returns the handle to the referenced choice defined on the given parameter element.

— Returns: choiceID of type String - Handle of the referenced choice
— Input: parameterBaseTypeID of type String - Handle to a parameter element

#### F.7.43.20 getClockEdgeAttribute

Description: Returns the attribute “clockEdge” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.21 getClockNameAttribute

Description: Returns the attribute “clockName” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.22 getClockSourceAttribute

Description: Returns the attribute “clockSource” defined on the given otherclockDriver element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.23 getComponentInstanceRefAttribute

Description: Returns the attribute “componentInstanceRef” defined on the given element

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.24 getComponentInstanceRefAttributeByID

Description: Returns the handle to the componentInstance referenced from the given element.

— Returns: componentInstanceID of type String - Handle to the referenced componentInstance element

— Input: elementID of type String - Handle to an element

#### F.7.43.25 getComponentRefAttribute

Description: Returns the attribute “componentRef” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.26 getComponentRefAttributeByID

Description: Returns the handle to the componentInstance defined on the given element.

— Returns: componentInstanceID of type String - Handle to the referenced componentInstance
— Input: interfaceRefID of type String - Handle to an interfaceRef element

#### F.7.43.27 getConfigGroupsAttribute

Description: Returns the attribute “configGroups” defined on the given parameter element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.28 getConstrainedAttributeValues

Description: Returns the attribute “constrained” list defined on the given wireTypeName element.

— Returns: attributeValue of type String - The attribute value list
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.29 getConstraintSetIdAttribute

Description: Returns the attribute “constraintSetId” defined on the given constraintSet element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.30 getCustomAttribute

Description: Returns the attribute “custom” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.31 getDataTypeAttribute

Description: Returns the attribute “dataType” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.32 getDataTypeDefinitionAttribute

Description: Returns the attribute “dataTypeDefinition” defined on the given parameter element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.33 getDefaultBooleanAttribute

Description: Returns the attribute “default” defined on the given logicalName element.

— Returns: attributeValue of type Boolean - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.34 getDelayTypeAttribute

Description: Returns the attribute “delayType” defined on the given timingConstraint element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.35 getDirectionAttribute

Description: Returns the attribute “direction” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.36 getDriverTypeAttribute

Description: Returns the attribute “driverType” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has the attribute “driverType”

#### F.7.43.37 getExactBooleanAttribute

Description: Returns the attribute “exact” defined on the given typeName element.

— Returns: attributeValue of type Boolean - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.38 getExternalDeclarationsBooleanAttribute

Description: Returns the attribute “externalDeclarations” defined on the given file isInclude element.

— Returns: attributeValue of type Boolean - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.39 getFieldRefAttribute

Description: Returns the attribute “fieldRef” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.40 getFieldRefAttributeByID

Description: Returns the handle to field referenced from the given fieldRef element.

— Returns: fieldID of type String - Handle to the referenced field element
— Input: fieldRefID of type String - Handle to a fieldRef element

#### F.7.43.41 getFileIdAttribute

Description: Returns the “fileId” attribute defined on the given file element.

— Returns: fileId of type String - The value of the fileId attribute
— Input: elementID of type String - Handle to a file element

#### F.7.43.42 getFlowTypeAttribute

Description: Returns the attribute “flowType” defined on the given isFlowControl element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.43 getForceBooleanAttribute

Description: Returns the attribute “force” defined on the given accessHandle element.

— Returns: attributeValue of type Boolean - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.44 getGroupAttribute

Description: Returns the attribute “group” defined on the given abstractorMode element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.45 getHelpAttribute

Description: Returns the attribute “help” defined on the given choice enumeration element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.46 getHiddenBooleanAttribute

Description: Returns the attribute “hidden” defined on the given element.

— Returns: attributeValue of type Boolean - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.47 getIdAttribute

Description: Returns the attribute “id” defined on the given element

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to

#### F.7.43.48 getImageIdAttribute

Description: Returns the attribute “imageId” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.49 getImageTypeAttribute

Description: Returns the attribute “imageType” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.50 getImplicitBooleanAttribute

Description: Returns the attribute “implicit” defined on the given typeName element.

— Returns: attributeValue of type Boolean - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.51 getIndexVarAttribute

Description: Returns the attribute “indexVar” defined on the given dim element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.52 getInitiatorRefAttribute

Description: Returns the attribute “initiatorRef” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.53 getInitiatorRefAttributeByID

Description: Returns the handle to the initiator defined on the given element.

— Returns: initiatorID of type String - Handle to the referenced initiator
— Input: elementID of type String - Handle to an element

#### F.7.43.54 getInterfaceModeAttribute

Description: Returns the attribute “interfaceMode” defined on the given monitor element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.55 getInvertAttribute

Description: Returns the attribute “invert” defined on the given portMap element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.56 getIsIOBooleanAttribute

Description: Returns the attribute “isIO” defined on the given subPort element.

— Returns: attributeValue of type Boolean - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.57 getLevelAttribute

Description: Returns the attribute “level” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.58 getLibextAttribute

Description: Returns the attribute “libext” defined on the given fileType element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.59 getLibraryAttribute

Description: Returns the attribute “library” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.60 getMandatoryBooleanAttribute

Description: Returns the attribute “mandatory” defined on the given extension element from payload.

— Returns: attributeValue of type Boolean - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.61 getMaximumAttribute

Description: Returns the attribute “maximum” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.62 getMaximumDoubleAttribute

Description: Returns the attribute “maximum” defined on the given element.

— Returns: attributeValue of type Double - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.63 getMaximumIntAttribute

Description: Returns the attribute “maximum” defined on the given element.

— Returns: attributeValue of type Long - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.64 getMemoryMapRefAttribute

Description: Returns the attribute “memoryMapRef” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.65 getMemoryMapRefAttributeByID

Description: Returns the handle to the memoryMap referenced from the given element.

— Returns: memoryMapID of type String - Handle to the referenced memoryMap
— Input: elementID of type String - Handle to an element

#### F.7.43.66 getMemoryReMapRefAttributeByID

Description: Returns the handle to the memoryRemap referenced from the given element.

— Returns: memoryRemapID of type String - Handle to the referenced memoryRemap
— Input: elementID of type String - Handle to an element

#### F.7.43.67 getMemoryRemapRefAttribute

Description: Returns the attribute “memoryRemapRef” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.68 getMinimumAttribute

Description: Returns the attribute “minimum” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.69 getMinimumDoubleAttribute

Description: Returns the attribute “minimum” defined on the given element.

— Returns: attributeValue of type Double - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.70 getMinimumIntAttribute

Description: Returns the attribute “minimum” defined on the given element.

— Returns: attributeValue of type Long - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.71 getMisalignmentAllowedBooleanAttribute

Description: Returns the attribute “MisalignmentAllowed” defined on the given element.

— Returns: attributeValue of type Boolean - The attribute value
— Input: elementID of type String - Handle to an element
— Input:

#### F.7.43.72 getModeRefAttribute

Description: Returns the attribute “modeRef” defined on the given element

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.73 getModifyAttribute

Description: Returns the attribute “modify” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.74 getMultipleGroupSelectionOperatorAttribute

Description: Returns the “multipleGroupSelectionOperato” attribute defined on the given groupSelector
element.

— Returns: multipleGroupSelectionOperator of type String - The value of the

multipleGroupSelectionOperator attribute

— Input: elementID of type String - Handle to a groupSelector element

#### F.7.43.75 getNameAttribute

Description: Returns the attribute “name” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.76 getOrderFloatAttribute

Description: Returns the attribute “order” defined on the given element.

— Returns: attributeValue of type Float - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.77 getOtherAnyAttribute

Description: Returns the value of the given anyAttribute name defined on the given element.

— Returns: value of type String - The attribute value
— Input: attributeContainerID of type String - Handle to an element containing the attribute
— Input: attributeName of type String - The attribute name

#### F.7.43.78 getOtherAttribute

Description: Returns the attribute “other” defined on the given cellFunction element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.79 getOtherAttributes

Description: Returns all the otherAttribute names defined on the given element.

— Returns: attributesName of type String - List of attributes names
— Input: attributeContainerID of type String - Handle to the container of the attributes

#### F.7.43.80 getPackedBooleanAttribute

Description: Returns the attribute “packed” defined on the given structured element.

— Returns: attributeValue of type Boolean - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.81 getParameterIdAttribute

Description: Returns the attribute “parameterId” defined on the given parameter element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.82 getPathAttribute

Description: Returns the attribute “path” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.83 getPhantomBooleanAttribute

Description: Returns the attribute “phantom” defined on the given element.

— Returns: attributeValue of type Boolean - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.84 getPortRefAttribute

Description: Returns the attribute “portRef” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.85 getPortRefAttributeByID

Description: Returns the handle to the port referenced from the given portSlice element.

— Returns: portID of type String - Handle to the referenced port element
— Input: portSliceIDOrInternalPortRef of type String - Handle to a portSlice element

#### F.7.43.86 getPowerDomainRefAttribute

Description: Returns the attribute “powerDomainRef” defined on the given element.

— Returns: attributeValue of type String - The attribute value

— Input: elementID of type String - Handle to an element

#### F.7.43.87 getPowerDomainRefAttributeByID

Description: Returns the handle to the powerDomain referenced from the port qualifier isPowerEn element.

— Returns: powerDomainID of type String - Handle to the referenced powerDomain element
— Input: powerEnID of type String - Handle to a powerEn element

#### F.7.43.88 getPrefixAttribute

Description: Returns the attribute “prefix” defined on the given parameter element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.89 getPriorityIntAttribute

Description: Returns the attribute “priority” defined on the given element.

— Returns: attributeValue of type Long - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.90 getPromptAttribute

Description: Returns the attribute “prompt” defined on the given parameter element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.91 getReferenceIdAttribute

Description: Returns the attribute “referenceId” defined on the given configurableElementValue element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.92 getRegisterFileRefAttribute

Description: Returns the attribute “registerFileRef” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.93 getRegisterFileRefAttributeByID

Description: Returns the handle to the registerFile referenced from the given registerFileRef element.

— Returns: registerFileRefID of type String - Handle to the referenced registerFile element
— Input: registerFileRefID of type String - Handle to a registerFileRef element

#### F.7.43.94 getRegisterRefAttribute

Description: Returns the attribute “registerRef” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.95 getReplicateBooleanAttribute

Description: Returns the attribute “replicate” defined on the given function element.

— Returns: attributeValue of type Boolean - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.96 getResetTypeRefAttribute

Description: Returns the “resetTypeRef” attribute defined on the given resetTypeReference element.

— Returns: resetTypeRef of type String - The value of the referenced resetType
— Input: elementID of type String - Handle to a resetTypeReference element

#### F.7.43.97 getResetTypeRefAttributeByID

Description: Returns the handle to the resetType element referenced from the given reset element.

— Returns: resetTypeID of type String - Handle to the referenced resetType element
— Input: resetID of type String - Handle to a reset element

#### F.7.43.98 getResolveAttribute

Description: Returns the attribute “resolve” defined on the given parameter element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.99 getScopeAttribute

Description: Returns the attribute “scope” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to : componentGenerator element

#### F.7.43.100 getSegmentRefAttribute

Description: Returns the attribute “segmentRef” defined on the given subSpaceMap element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.101 getSegmentRefAttributeByID

Description: Returns the handle to the segment referenced from the given subspaceMap element.

— Returns: segmentID of type String - Handle to the referenced segment
— Input: subSpaceMapID of type String - Handle to a subspaceMap element

#### F.7.43.102 getSignAttribute

Description: Returns the attribute “sign” defined on the given parameter element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.103 getStrictBooleanAttribute

Description: Returns the attribute “strict” defined on the given language element.

— Returns: attributeValue of type Boolean - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.104 getSubPortRefAttribute

Description: Returns the attribute “subPortRef” defined on the given subPortReference element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.105 getSubPortRefAttributeByID

Description: Returns the handle to the subPort referenced from the given subPortReference.

— Returns: subPortID of type String - Handle to the referenced subPort element
— Input: subPortReferenceID of type String - Handle to a subPortReference element

#### F.7.43.106 getTestConstraintAttribute

Description: Returns the attribute “testConstraint” defined on the given testable element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.107 getTextAttribute

Description: Returns the attribute “text” defined on the given choice enumeration element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.108 getTypeAttribute

Description: Returns the attribute “type” defined on the given parameter element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.109 getTypeDefinitionsAttribute

Description: Returns the attribute “typeDefinitions” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.110 getUniqueBooleanAttribute

Description: Returns the “unique” boolean attribute defined on the given generatorChainSelector element.

— Returns: isUnique of type Boolean - The value of the unique attribute (false if not defined)
— Input: elementID of type String - Handle to a generatorChainSelector element

#### F.7.43.111 getUnitAttribute

Description: Returns the attribute “unit” defined on the given parameter element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.112 getUnitsAttribute

Description: Returns the attribute “units” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.113 getUsageAttribute

Description: Returns the attribute “usage” defined on the given enumeratedValue element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.114 getUsageTypeAttribute

Description: Returns the attribute “usageType” defined on the given parameter element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.115 getUserAttribute

Description: Returns the attribute “user” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.116 getVectorIdAttribute

Description: Returns the attribute “vectorId” of the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.117 getVendorAttribute

Description: Returns the attribute “vendor” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.118 getVersionAttribute

Description: Returns the attribute “version” defined on the given element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element

#### F.7.43.119 getViewRefAttribute

Description: Returns the attribute “viewRef” defined on the given view element.

— Returns: attributeValue of type String - The attribute value
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.43.120 getViewRefAttributeByID

Description: Returns the handle to view referenced from the given viewConfiguration or view element.

— Returns: viewID of type String - Handle to the referenced view element
— Input: viewConfigurationOrViewID of type String - Handle to a viewConfiguration element

or a view

### F.7.44 Element attribute (EXTENDED)

#### F.7.44.1 addConstrainedAttribute

Description: Adds the attribute “constrained” in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a wireTypeName element
— Input: constrained of type String - Attribute value

#### F.7.44.2 isSetAttribute

Description: Checks if the given attribute is set or not.

— Returns: isSet of type Boolean - True if the attribute is defined; False otherwise
— Input: elementID of type String - Handle to the parent of the attribute to check
— Input: attributeName of type String - The attribute name

#### F.7.44.3 removeAllBitsAttribute

Description: Removes the attribute “allBits” from the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a wirePort width element

#### F.7.44.4 removeAppendAttribute

Description: Removes the attribute “append” of the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a file buildCommand flags element

#### F.7.44.5 removeArrayIdAttribute

Description: Removes the attribute “arrayId” of the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element

#### F.7.44.6 removeAttribute

Description: Removes the given attribute name from its containing element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element that has an attribute
— Input: name of type String - Attribute name

#### F.7.44.7 removeCellStrengthAttribute

Description: Removes the attribute “cellStrength” from the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a cellSpecification element

#### F.7.44.8 removeChoiceRefAttribute

Description: Removes the attribute “choiceRef” in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a parameter element

#### F.7.44.9 removeClockEdgeAttribute

Description: Removes the value of the element clockEdge attribute.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to the element

#### F.7.44.10 removeClockNameAttribute

Description: Removes the value of the element clockName attribute.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to the element

#### F.7.44.11 removeClockSourceAttribute

Description: Removes the attribute “clockSource” from the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an otherclockDriver element

#### F.7.44.12 removeConstrainedAttribute

Description: Removes the given constrained from the attribute “constrained” list in the given element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a wireTypeName element
— Input: constrained of type String - Attribute expression

#### F.7.44.13 removeConstraintSetIdAttribute

Description: Removes the value of the element constraintSetId attribute.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to the element

#### F.7.44.14 removeDataTypeAttribute

Description: Removes the attribute “dataType” in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element

#### F.7.44.15 removeDataTypeDefinitionAttribute

Description: Removes the attribute “dataTypeDefinition” in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a parameter element

#### F.7.44.16 removeDefaultAttribute

Description: Removes the default attribute of the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.44.17 removeDelayTypeAttribute

Description: Removes the value of the element clockEdge attribute.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to the element

#### F.7.44.18 removeDirectionAttribute

Description: Removes the attribute “direction” of the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element

#### F.7.44.19 removeDriverTypeAttribute

Description: Removes the attribute “driverType” to the given expression for the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.44.20 removeExternalDeclarationsAttribute

Description: Removes the externalDeclarations attribute of the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.44.21 removeFileIdAttribute

Description: Removes the fileId attribute of the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.44.22 removeFlowTypeAttribute

Description: Removes the attribute “flowType” from the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an isFlowControl element

#### F.7.44.23 removeForceAttribute

Description: Removes the value of the element force attribute.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to the element

#### F.7.44.24 removeGroupAttribute

Description: Removes the attribute “group” in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to element which contains the id.

#### F.7.44.25 removeHelpAttribute

Description: Removes the value of the element help attribute.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to the element

#### F.7.44.26 removeHiddenAttribute

Description: Removes the value of the element hidden attribute.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to the element

#### F.7.44.27 removeIdAttribute

Description: Removes the attribute “id” in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to element which contains the id.

#### F.7.44.28 removeImageTypeAttribute

Description: Removes the imageType attribute of the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.44.29 removeImplicitAttribute

Description: Removes the attribute “implicit” of the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a typeName element

#### F.7.44.30 removeInvertAttribute

Description: Removes the value of the element invert attribute.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to the element

#### F.7.44.31 removeIsIOAttribute

Description: Removes the attribute “isIO” from the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a subPort element

#### F.7.44.32 removeLevelAttribute

Description: Removes the attribute “level” from the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element

#### F.7.44.33 removeLibextAttribute

Description: Removes the libext attribute of the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.44.34 removeMaximumAttribute

Description: Removes the maximum attribute of the given numeric expression.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an expression element

#### F.7.44.35 removeMinimumAttribute

Description: Removes the minimum attribute of the given numeric expression.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an expression element

#### F.7.44.36 removeMisalignmentAllowedAttribute

Description: Removes the value of the element misalignmentAllowed attribute.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to the element

#### F.7.44.37 removeModeAttribute

Description: Removes the value of the element mode attribute.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to the element

#### F.7.44.38 removeModifyAttribute

Description: Removes the value of the element modify attribute.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to the element

#### F.7.44.39 removeMultipleGroupSelectionOperatorAttribute

Description: Removes the value of the element multipleGroupSelectionOperator attribute.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a groupSelector

#### F.7.44.40 removeOrderAttribute

Description: Removes the attribute “order” in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a parameter element

#### F.7.44.41 removeOtherAnyAttribute

Description: Removes the otherAny attribute name and value on the given element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: attributeContainerID of type String - Handle to the element containing the attribute
— Input: attributeName of type String - Name of the attribute

#### F.7.44.42 removeOtherAttribute

Description: Removes the value of the element other attribute.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to the element

#### F.7.44.43 removePackedAttribute

Description: Removes the attribute “packed” from the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a structured element

#### F.7.44.44 removeParameterIdAttribute

Description: Removes the attribute “parameterId” in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a parameter element

#### F.7.44.45 removePathAttribute

Description: Removes the value of the element path attribute.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to the element

#### F.7.44.46 removePhantomAttribute

Description: Removes the attribute “phantom” of the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element

#### F.7.44.47 removePowerDomainRefAttribute

Description: Removes the attribute “powerDomainRef” from the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element

#### F.7.44.48 removePrefixAttribute

Description: Removes the attribute “prefix” in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a parameter element

#### F.7.44.49 removePromptAttribute

Description: Removes the attribute “prompt” in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a parameter element

#### F.7.44.50 removeReplicateAttribute

Description: Removes the attribute “replicate” of the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a function element

#### F.7.44.51 removeResetTypeRefAttribute

Description: Removes the value of the element resetTypeRef attribute.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to the element

#### F.7.44.52 removeResolveAttribute

Description: Removes the attribute “resolve” in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a parameter element

#### F.7.44.53 removeScopeAttribute

Description: Removes the scope attribute of the element componentGenerator or abstractorGenerator
attribute.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element

#### F.7.44.54 removeSegmentRefAttribute

Description: Removes the attribute “segmentRef” of the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a subSpaceMap element

#### F.7.44.55 removeSignAttribute

Description: Removes the attribute “sign” in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a parameter element

#### F.7.44.56 removeStrictAttribute

Description: Removes the attribute “strict” from the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a language element

#### F.7.44.57 removeTestConstraintAttribute

Description: Removes the attribute “testConstraint” of the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a testable element

#### F.7.44.58 removeTextAttribute

Description: Removes the value of the element text attribute.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element

#### F.7.44.59 removeTypeAttribute

Description: Removes the attribute “type” in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to parameter element

#### F.7.44.60 removeUniqueAttribute

Description: Removes the value of the element unique attribute.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element

#### F.7.44.61 removeUnitAttribute

Description: Removes the attribute “unit” in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a parameter element

#### F.7.44.62 removeUnitsAttribute

Description: Removes the attribute “units” from the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a clockPeriod or clockPulseOffset or

clockPulseDuration element

#### F.7.44.63 removeUsageTypeAttribute

Description: Removes the attribute “usageType” in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a parameter element

#### F.7.44.64 removeUserAttribute

Description: Removes the user attribute of the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element that has an attribute

#### F.7.44.65 removeVectorIdAttribute

Description: Removes the attribute “vectorId” of the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element

#### F.7.44.66 setAddressBlockRefAttribute

Description: Sets the attribute “addressBlockRef” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an addressBlockRef element
— Input: expression of type String - Attribute expression

#### F.7.44.67 setAddressSpaceRefAttribute

Description: Sets the attribute “addressSpaceRef” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: expression of type String - Attribute expression

#### F.7.44.68 setAllBitsBooleanAttribute

Description: Sets the attribute “allBits” to the given expression in the element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a wirePort width element
— Input: value of type Boolean - Attribute value

#### F.7.44.69 setAllLogicalDirectionsAllowedBooleanAttribute

Description: Sets the attribute “allLogicalDirectionsAllowed” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element that has an attribute
— Input: expression of type Boolean - Attribute expression

#### F.7.44.70 setAllLogicalInitiativesAllowedBooleanAttribute

Description: Sets the attribute “allLogicalInitiativesAllowed” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element that has an attribute
— Input: expression of type Boolean - Attribute expression

#### F.7.44.71 setAlternateRegisterRefAttribute

Description: Sets the attribute “alternateRegisterRef” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: expression of type String - Attribute expression

#### F.7.44.72 setAppendBooleanAttribute

Description: Sets the attribute “append” to the given value in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a file buildCommand flags element
— Input: append of type Boolean - Attribute value

#### F.7.44.73 setArrayIdAttribute

Description: Sets the attribute “arrayId” in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: arrayId of type String - Attribute value

#### F.7.44.74 setBankAlignmentAttribute

Description: Sets the attribute “bankAlignment” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: expression of type String - Attribute expression

#### F.7.44.75 setBankRefAttribute

Description: Sets the attribute “bankRef” to the given expression in the given memoryMapRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element that has an attribute
— Input: expression of type String - Attribute expression

#### F.7.44.76 setBusRefAttribute

Description: Sets the attribute “busRef” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: expression of type String - Attribute expression

#### F.7.44.77 setCellStrengthAttribute

Description: Sets the attribute “cellStrength” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a cellSpecification element
— Input: expression of type String - Attribute expression

#### F.7.44.78 setChoiceRefAttribute

Description: Sets the attribute “choiceRef” to the given value in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a parameter element
— Input: expression of type String - Attribute expression

#### F.7.44.79 setClockEdgeAttribute

Description: Sets the attribute “clockEdge” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: expression of type String - Attribute expression

#### F.7.44.80 setClockNameAttribute

Description: Sets the attribute “clockName” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: expression of type String - Attribute expression

#### F.7.44.81 setClockSourceAttribute

Description: Sets the attribute “clockSource” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an otherClockDriver element
— Input: expression of type String - Attribute expression

#### F.7.44.82 setComponentInstanceRefAttribute

Description: Sets the attribute “componentInstanceRef” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: expression of type String - Attribute expression

#### F.7.44.83 setComponentRefAttribute

Description: Sets the attribute “componentRef” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: expression of type String - Attribute expression

#### F.7.44.84 setConfigGroupsAttribute

Description: Sets the attribute “configGroups” to the given value in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a parameter element
— Input: configGroups of type String - Attribute value

#### F.7.44.85 setConstraintSetIdAttribute

Description: Sets the attribute “constraintSetId” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a constraintSet element
— Input: expression of type String - Attribute expression

#### F.7.44.86 setCustomAttribute

Description: Sets the attribute “custom” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: expression of type String - Attribute expression

#### F.7.44.87 setDataTypeAttribute

Description: Sets the attribute “dataType” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: expression of type String - Attribute expression

#### F.7.44.88 setDataTypeDefinitionAttribute

Description: Sets the attribute “dataTypeDefinition” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a parameter element
— Input: expression of type String - Attribute expression

#### F.7.44.89 setDefaultBooleanAttribute

Description: Sets the attribute “default” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a file logicalName element
— Input: defaultValue of type Boolean - Attribute value

#### F.7.44.90 setDelayTypeAttribute

Description: Sets the attribute “delayType” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a timingConstraint element
— Input: expression of type String - Attribute expression

#### F.7.44.91 setDirectionAttribute

Description: Sets the attribute “direction” in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: direction of type String - Attribute value

#### F.7.44.92 setDriverTypeAttribute

Description: Sets the attribute “driverType” to the given expression for the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element that has an attribute
— Input: driverType of type String - The driver type value

#### F.7.44.93 setExactBooleanAttribute

Description: Sets the attribute “exact” in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a typeName element
— Input: exact of type Boolean - Attribute value

#### F.7.44.94 setExternalDeclarationsBooleanAttribute

Description: Sets the attribute “externalDeclarations” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a file isInclude element
— Input: externalDeclarations of type Boolean - Attribute value

#### F.7.44.95 setFieldRefAttribute

Description: Sets the attribute “fieldRef” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: expression of type String - Attribute expression

#### F.7.44.96 setFileIdAttribute

Description: Sets the attribute “fileId” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a file buildCommand flags element
— Input: expression of type String - Attribute expression

#### F.7.44.97 setFlowTypeAttribute

Description: Sets the attribute “flowType” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an isFlowControl element
— Input: expression of type String - Attribute expression

#### F.7.44.98 setForceBooleanAttribute

Description: Sets the attribute “force” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an accessHandle element
— Input: force of type Boolean - Attribute expression

#### F.7.44.99 setGroupAttribute

Description: Sets the attribute “group” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an abstractorMode element
— Input: expression of type String - Attribute expression

#### F.7.44.100 setHelpAttribute

Description: Sets the attribute “help” to the given value for the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: help of type String - ChoiceEnumeration help

#### F.7.44.101 setHiddenBooleanAttribute

Description: Sets the attribute “hidden” to the given value in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: hidden of type Boolean - True if the given element is hidden

#### F.7.44.102 setIdAttribute

Description: Sets the attribute “id” to the given value in the given element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: id of type String - Attribute value

#### F.7.44.103 setImageIdAttribute

Description: Sets the attribute “imageId” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element that has an attribute
— Input: imageId of type String - Attribute value

#### F.7.44.104 setImageTypeAttribute

Description: Sets the attribute “imageType” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element that has an attribute
— Input: imageType of type String - Attribute value

#### F.7.44.105 setImplicitBooleanAttribute

Description: Sets the attribute “implicit” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a typeName element
— Input: implicit of type Boolean - Attribute value

#### F.7.44.106 setIndexVarAttribute

Description: Sets the attribute “indexVar” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a dim element
— Input: expression of type String - Attribute expression

#### F.7.44.107 setInitiatorRefAttribute

Description: Sets the attribute “initiatorRef” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: expression of type String - Attribute expression

#### F.7.44.108 setInterfaceModeAttribute

Description: Sets the attribute “interfaceMode” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a monitor element
— Input: expression of type String - Attribute expression

#### F.7.44.109 setInvertAttribute

Description: Sets the attribute “invert” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a portMap element
— Input: expression of type String - Attribute expression

#### F.7.44.110 setIsIOBooleanAttribute

Description: Sets the attribute “isIO” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a subPort element
— Input: value of type Boolean - Attribute value

#### F.7.44.111 setLevelAttribute

Description: Sets the attribute “level” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: expression of type String - Attribute expression

#### F.7.44.112 setLibextAttribute

Description: Sets the attribute “libext” to the given expression in the given fileType element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element that has an attribute
— Input: expression of type String - Attribute expression

#### F.7.44.113 setLibraryAttribute

Description: Sets the attribute “library” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: expression of type String - Attribute expression

#### F.7.44.114 setMandatoryBooleanAttribute

Description: Sets the attribute “mandatory” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a payload extension element
— Input: expression of type Boolean - Attribute boolean value

#### F.7.44.115 setMaximumAttribute

Description: Sets the attribute “maximum” to the given value in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: value of type String - Attribute value

#### F.7.44.116 setMaximumDoubleAttribute

Description: Sets the attribute “maximum” in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: value of type Double - Attribute value

#### F.7.44.117 setMaximumIntAttribute

Description: Sets the attribute “maximum” in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: value of type Long - Attribute value

#### F.7.44.118 setMemoryMapRefAttribute

Description: Sets the attribute “memoryMapRef” to the given expression in the given memoryMapRef
element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element that has an attribute
— Input: expression of type String - Attribute expression

#### F.7.44.119 setMemoryRemapRefAttribute

Description: Sets the attribute “memoryRemapRef” to the given expression in the given memoryMapRef
element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element that has an attribute
— Input: expression of type String - Attribute expression

#### F.7.44.120 setMinimumAttribute

Description: Sets the attribute “minimum” to the given value in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: value of type String - Attribute value

#### F.7.44.121 setMinimumDoubleAttribute

Description: Sets the attribute “minimum” in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: value of type Double - Attribute value

#### F.7.44.122 setMinimumIntAttribute

Description: Sets the attribute “minimum” in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: value of type Long - Attribute value

#### F.7.44.123 setMisalignmentAllowedBooleanAttribute

Description: Sets the attribute “misalignmentAllowed” to the given value in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: misalignmentAllowed of type Boolean - True if the given element is

misalignmentAllowed

#### F.7.44.124 setModeRefAttribute

Description: Sets the attribute “modeRef” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)

— Input: elementID of type String - Handle to a view element
— Input: expression of type String - Attribute expression

#### F.7.44.125 setModifyAttribute

Description: Sets the attribute “modify” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: expression of type String - Attribute expression

#### F.7.44.126 setMultipleGroupSelectionOperatorAttribute

Description: Sets the attribute “multipleGroupSelectionOperator” to the given value in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a groupSelector element
— Input: multipleGroupSelectionOperator of type String - Specifies the OR or AND

selection operator if there is more than one group name

#### F.7.44.127 setNameAttribute

Description: Sets the attribute “name” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: expression of type String - Attribute expression

#### F.7.44.128 setOrderFloatAttribute

Description: Sets the attribute “order” to the given value in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a parameter element
— Input: order of type Double - Attribute value

#### F.7.44.129 setOtherAnyAttribute

Description: Sets the otherAny attribute name and value on the given element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: attributeContainerID of type String - Handle to the element containing the attribute
— Input: attributeName of type String - Name of the attribute
— Input: value of type String - Value of the attribute

#### F.7.44.130 setOtherAttribute

Description: Sets the attribute “other” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a cellFunction element
— Input: expression of type String - Attribute expression

#### F.7.44.131 setPackedBooleanAttribute

Description: Sets the attribute “packed” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a structured element
— Input: packed of type Boolean - Attribute value

#### F.7.44.132 setParameterIdAttribute

Description: Sets the attribute “parameterId” to the given value in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a parameter element
— Input: expression of type String - Attribute expression

#### F.7.44.133 setPathAttribute

Description: Sets the attribute “path” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: expression of type String - Attribute expression

#### F.7.44.134 setPhantomBooleanAttribute

Description: Sets the attribute “phantom” to the given value in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: hidden of type Boolean - True if the given element is hidden

#### F.7.44.135 setPortRefAttribute

Description: Sets the attribute “portRef” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: expression of type String - Attribute expression

#### F.7.44.136 setPowerDomainRefAttribute

Description: Sets the attribute “powerDomainRef” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: expression of type String - Attribute expression

#### F.7.44.137 setPrefixAttribute

Description: Sets the attribute “prefix” to the given value in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a parameter element
— Input: expression of type String - Attribute expression

#### F.7.44.138 setPriorityIntAttribute

Description: Sets the attribute “priority” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a modeRef element
— Input: expression of type Long - Attribute expression

#### F.7.44.139 setPromptAttribute

Description: Sets the attribute “prompt” to the given value in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a parameter element
— Input: expression of type String - Attribute expression

#### F.7.44.140 setReferenceIdAttribute

Description: Sets the attribute “referenceId” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a configurableElementValue element
— Input: expression of type String - Attribute expression

#### F.7.44.141 setRegisterFileRefAttribute

Description: Sets the attribute “registerFileRef” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: expression of type String - Attribute expression

#### F.7.44.142 setRegisterRefAttribute

Description: Sets the attribute “registerRef” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: expression of type String - Attribute expression

#### F.7.44.143 setReplicateBooleanAttribute

Description: Sets the attribute “replicate” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a function element
— Input: replicate of type Boolean - Attribute value

#### F.7.44.144 setResetTypeRefAttribute

Description: Sets the attribute “resetTypeRef” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: expression of type String - Attribute expression

#### F.7.44.145 setResolveAttribute

Description: Sets the attribute “resolve” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a parameter element
— Input: expression of type String - Attribute expression

#### F.7.44.146 setScopeAttribute

Description: Sets the attribute “scope” to the given value in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a componentGenerator element
— Input: scope of type String - The scope attribute applies to component generators and specifies
whether the generator should be run for each instance of the entity (or module) or just once for all
instances of the entity.

#### F.7.44.147 setSegmentRefAttribute

Description: Sets the attribute “segmentRef” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a subSpaceMap element
— Input: expression of type String - Attribute expression

#### F.7.44.148 setSignAttribute

Description: Sets the attribute “sign” to the given value in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a parameter element
— Input: expression of type String - Attribute expression

#### F.7.44.149 setStrictBooleanAttribute

Description: Sets the attribute “strict” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a language element
— Input: strict of type Boolean - Attribute expression

#### F.7.44.150 setSubPortRefAttribute

Description: Sets the attribute “subPortRef” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a subPortReference element
— Input: expression of type String - Attribute expression

#### F.7.44.151 setTestConstraintAttribute

Description: Sets the attribute “testConstraint” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a testable element

— Input: testConstraint of type String - Attribute value

#### F.7.44.152 setTextAttribute

Description: Sets the attribute “text” to the given value for the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: text of type String - ChoiceEnumeration text

#### F.7.44.153 setTypeAttribute

Description: Sets the attribute “type” to the given value in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to parameter element
— Input: expression of type String - Attribute expression

#### F.7.44.154 setTypeDefinitionsAttribute

Description: Sets the attribute “typeDefinitions” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: expression of type String - Attribute expression

#### F.7.44.155 setUniqueBooleanAttribute

Description: Sets the attribute “unique” to the given value in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a generatorChainSelector element
— Input: unique of type Boolean - True if the given element is unique

#### F.7.44.156 setUnitAttribute

Description: Sets the attribute “unit” to the given value in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a parameter element
— Input: expression of type String - Attribute expression

#### F.7.44.157 setUnitsAttribute

Description: Sets the attribute “units” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a clockPeriod or clockPulseOffset or clockPulseDur-

ation element

— Input: expression of type String - Attribute expression

#### F.7.44.158 setUsageAttribute

Description: Sets the attribute “usage” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)

— Input: elementID of type String - Handle to an enumeratedValue element
— Input: expression of type String - Attribute expression

#### F.7.44.159 setUsageTypeAttribute

Description: Sets the attribute “usageType” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a parameter element
— Input: expression of type String - Attribute expression

#### F.7.44.160 setUserAttribute

Description: Sets the attribute “user” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an isFlowControl or isUser or fileType element
— Input: expression of type String - Attribute expression

#### F.7.44.161 setVectorIdAttribute

Description: Sets the attribute “vectorId” in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: vectorId of type String - Attribute value

#### F.7.44.162 setVendorAttribute

Description: Sets the attribute “vendor” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: expression of type String - Attribute expression

#### F.7.44.163 setVersionAttribute

Description: Sets the attribute “version” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element
— Input: expression of type String - Attribute expression

#### F.7.44.164 setViewRefAttribute

Description: Sets the attribute “viewRef” to the given expression in the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a view element
— Input: expression of type String - Attribute expression

### F.7.45 File builder (BASE)

#### F.7.45.1 getBuildCommandCommand

Description: Returns the command defined on the given buildCommand element.

— Returns: commandValue of type String - The command value
— Input: buildCommandID of type String - Handle to a buildCommand element

#### F.7.45.2 getBuildCommandCommandExpression

Description: Returns the command expression defined on the given buildCommand element.

— Returns: baseAddressExpression of type String - The command expression
— Input: buildCommandID of type String - Handle to a buildCommand element

#### F.7.45.3 getBuildCommandCommandID

Description: Returns the handle to the command defined on the given buildCommand element.

— Returns: commandID of type String - Handle to the command element
— Input: buildCommandID of type String - Handle to a buildCommand element

#### F.7.45.4 getBuildCommandFlags

Description: Returns the flags defined on the given buildCommand element.

— Returns: flagsValue of type String - The buildCommand flags
— Input: buildCommandID of type String - Handle to a buildCommand element

#### F.7.45.5 getBuildCommandFlagsExpression

Description: Returns the flags expression defined on the given buildCommand element.

— Returns: flagsExpression of type String - The buildCommand flags expression
— Input: buildCommandID of type String - Handle to a buildCommand element

#### F.7.45.6 getBuildCommandFlagsID

Description: Returns the handle to the flags defined on the given buildCommand element.

— Returns: FlagsID of type String - Handle to the flags element
— Input: buildCommandID of type String - Handle to a buildCommand element

#### F.7.45.7 getBuildCommandReplaceDefaultFlags

Description: Returns the replaceDefaultFlags value defined on the given buildCommand element.

— Returns: flagsValue of type Boolean - The buildCommands replaceDefaultFlags value
— Input: buildCommandID of type String - Handle to a buildCommand element

#### F.7.45.8 getBuildCommandReplaceDefaultFlagsID

Description: Returns the handle to the replaceDefaultFlags defined on the given buildCommand element.

— Returns: replaceDefaultFlagsID of type String - Handle to the replaceDefaultFlags element
— Input: buildCommandID of type String - Handle to a buildCommand element

#### F.7.45.9 getBuildCommandTargetName

Description: Returns the targetName defined on the given buildCommand element.

— Returns: targetName of type String - The buildCommands target name
— Input: buildCommandID of type String - Handle to a buildCommand element

#### F.7.45.10 getBuildCommandTargetNameExpression

Description: Returns the handle to the targetName defined on the given buildCommand element.

— Returns: targetNameID of type String - Handle to the targetName element
— Input: buildCommandID of type String - Handle to a buildCommand element

#### F.7.45.11 getExecutableImageFileBuilderIDs

Description: Returns the handles to all the fileBuilders defined on the given executableImage element.

— Returns: fileBuilderIDs of type String - List of handles to the fileBuilder elements
— Input: executableImageID of type String - Handle to an executableImage element

#### F.7.45.12 getExecutableImageFileSetRefIDs

Description: Returns the handles to all the fileSetRefs defined on the given executableImage element.

— Returns: fileSetRefIDs of type String - List of handles to the fileSetRef elements
— Input: executableImageID of type String - Handle to an executableImage element

#### F.7.45.13 getExecutableImageLanguageToolsID

Description: Returns the handle to the languageTools defined on the given executableImage element.

— Returns: languageToolsID of type String - Handle to the languageTools element
— Input: executableImageID of type String - Handle to an executableImage element

#### F.7.45.14 getExecutableImageLinker

Description: Returns the linker defined on the given executableImage element.

— Returns: linker of type String - The linker value
— Input: executableImageID of type String - Handle to an executableImage element

#### F.7.45.15 getExecutableImageLinkerCommandFileID

Description: Returns the handle to the linkerCommandFile defined on the given executableImage element.

— Returns: linkerCommandFileID of type String - Handle to a linkerCommandFile element
— Input: executableImageID of type String - Handle to an executableImage element

#### F.7.45.16 getExecutableImageLinkerExpression

Description: Returns the linker expression defined on the given executableImage element.

— Returns: linkerExpression of type String - The linker expression
— Input: executableImageID of type String - Handle to an executableImage element

#### F.7.45.17 getExecutableImageLinkerFlags

Description: Returns the linkerFlags defined on the given executableImage element.

— Returns: linkerFlags of type String - The linker flags
— Input: executableImageID of type String - Handle to an executableImage element

#### F.7.45.18 getExecutableImageLinkerFlagsExpression

Description: Returns the linkerFlags expression defined on the given executableImage element.

— Returns: linkerFlagsExpression of type String - The linkerFlags expression
— Input: executableImageID of type String - Handle to an executableImage element

#### F.7.45.19 getFileBuildCommandID

Description: Returns the hande to the buildCommand defined on the given file element.

— Returns: buildCommandID of type String - Handle to the buildCommand element
— Input: fileID of type String - Handle to a file element

#### F.7.45.20 getFileBuilderCommand

Description: Returns the command element defined on the given fileBuilder element.

— Returns: command of type String - The command value
— Input: fileBuilderID of type String - Handle to a fileBuilder element

#### F.7.45.21 getFileBuilderCommandExpression

Description: Returns the command expression defined on the given fileBuilder element.

— Returns: commandExpression of type String - The command expression
— Input: fileBuilderID of type String - Handle to a fileBuilder element

#### F.7.45.22 getFileBuilderCommandID

Description: Returns the handle to the command defined on the given fileBuilder element.

— Returns: CommandID of type String - Handle to the command
— Input: fileBuilderID of type String - Handle to a fileBuilder element

#### F.7.45.23 getFileBuilderFileType

Description: Returns the fileType element defined on the given fileBuilder element.

— Returns: fileType of type String - The fileType value
— Input: fileBuilderID of type String - Handle to a fileBuilder element

#### F.7.45.24 getFileBuilderFileTypeID

Description: Returns the handle to the fileType defined on the given fileBuilder element.

— Returns: fileTypeID of type String - Handle to the fileType element
— Input: fileBuilderID of type String - Handle to a fileBuilder element

#### F.7.45.25 getFileBuilderFlags

Description: Returns the flags element defined on the given fileBuilder element.

— Returns: flags of type String - The flags value
— Input: fileBuilderID of type String - Handle to a fileBuilder element

#### F.7.45.26 getFileBuilderFlagsExpression

Description: Returns the flags expression defined on the given fileBuilder element.

— Returns: flagsExpression of type String - The flags expression
— Input: fileBuilderID of type String - Handle to a fileBuilder element

#### F.7.45.27 getFileBuilderFlagsID

Description: Returns the handle to the flags defined on the given fileBuilder element.

— Returns: FlagsID of type String - Handle to flags element
— Input: fileBuilderID of type String - Handle to a fileBuilder element

#### F.7.45.28 getFileBuilderReplaceDefaultFlags

Description: Returns the replaceDefaultFlags element defined on the given fileBuilder element.

— Returns: value of type Boolean - The replaceDefaultFlags value
— Input: fileBuilderID of type String - Handle to a fileBuilder element

#### F.7.45.29 getFileBuilderReplaceDefaultFlagsExpression

Description: Returns the replaceDefaultFlags expression defined on the given fileBuilder element.

— Returns: valueExpression of type String - The replaceDefaultFlags expression
— Input: fileBuilderID of type String - Handle to a fileBuilder element

#### F.7.45.30 getFileBuilderReplaceDefaultFlagsID

Description: Returns the handle to the replaceDefaultFlags defined on the given fileBuilder element.

— Returns: ReplaceDefaultFlagsID of type String - Handle to the replaceDefaultFlags element
— Input: fileBuilderID of type String - Handle to a fileBuilder element

#### F.7.45.31 getGeneratorRefByID

Description: Returns the handle to the generator referenced from the given generatorRef element.

— Returns: generatorID of type String - Handle to the referenced generator element
— Input: generatorRefID of type String - Handle to a generatorRef element

#### F.7.45.32 getLanguageToolsFileBuilderIDs

Description: Returns the handles to all the fileBuilders defined on the given languageTools element.

— Returns: fileBuilderIDs of type String - List of handles to the fileBuilder elements
— Input: languageToolsID of type String - Handle to a languageTools element

#### F.7.45.33 getLanguageToolsLinker

Description: Returns the linker value defined on the given languageTools element.

— Returns: linker of type String - The linker value
— Input: languageToolsID of type String - Handle to a languageTools element

#### F.7.45.34 getLanguageToolsLinkerCommandFileID

Description: Returns the handle to the linkerCommandFile defined on the given languageTools element.

— Returns: linkerCommandFileID of type String - Handle to the linkerCommandFile element
— Input: languageToolsID of type String - Handle to a languageTools element

#### F.7.45.35 getLanguageToolsLinkerExpression

Description: Returns the linker expression defined on the given languageTools element.

— Returns: linker of type String - The linker expression
— Input: languageToolsID of type String - Handle to a languageTools element

#### F.7.45.36 getLanguageToolsLinkerFlags

Description: Returns the linkerFlags value defined on the given languageTools element.

— Returns: linkerFlags of type String - The linkerFlags value on a languageTools element
— Input: languageToolsID of type String - Handle to a languageTools element

#### F.7.45.37 getLanguageToolsLinkerFlagsExpression

Description: Returns the linkerFlags expression defined on the given languageTools element.

— Returns: linkerFlags of type String - The linkerFlags expression on a languageTools element
— Input: languageToolsID of type String - Handle to a languageTools element

#### F.7.45.38 getLanguageToolsLinkerFlagsID

Description: Returns the handle to the linkerFlags defined on the given languageTools element.

— Returns: linkerFlagsID of type String - Handle to the linkerFlags element
— Input: languageToolsID of type String - Handle to a languageTools element

#### F.7.45.39 getLanguageToolsLinkerID

Description: Returns the handle to the linker defined on the given languageTools element.

— Returns: linkerID of type String - Handle to the linker element
— Input: languageToolsID of type String - Handle to a languageTools element

#### F.7.45.40 getLinkerCommandFileCommandLineSwitch

Description: Returns the commandLineSwitch value defined on the given linkerCommandFile element.

— Returns: commandLineSwitch of type String - The commandLineSwitch value
— Input: linkerCommandFileID of type String - Handle to a linkerCommandFile element

#### F.7.45.41 getLinkerCommandFileCommandLineSwitchExpression

Description: Returns the commandLineSwitch expression defined on the given linkerCommandFile
element.

— Returns: commandLineSwitch of type String - The commandLineSwitch expression
— Input: linkerCommandFileID of type String - Handle to a linkerCommandFile element

#### F.7.45.42 getLinkerCommandFileCommandLineSwitchID

Description: Returns the handle to the commandLineSwitch defined on the given linkerCommandFile
element.

— Returns: commandLineSwitchID of type String - Handle to the commandLineSwitch element
— Input: linkerCommandFileID of type String - Handle to a linkerCommandFile element

#### F.7.45.43 getLinkerCommandFileEnable

Description: Returns the enable value defined on the given linkerCommandFile element.

— Returns: value of type Boolean - The enable value
— Input: linkerCommandFileID of type String - Handle to a linkerCommandFile element

#### F.7.45.44 getLinkerCommandFileEnableExpression

Description: Returns the enable expression defined on the given linkerCommandFile.

— Returns: valueExpression of type String - The enable expression
— Input: linkerCommandFileID of type String - Handle to a linkerCommandFile

#### F.7.45.45 getLinkerCommandFileEnableID

Description: Returns the handle to the enable element defined on the given linkerCommandFile element.

— Returns: enableID of type String - Handle to the enable element
— Input: linkerCommandFileID of type String - Handle to a linkerCommandFile element

#### F.7.45.46 getLinkerCommandFileGeneratorRefByID

Description: Returns the generatorID defined on the given linkerCommandFile element.

— Returns: generatorID of type String - The referenced generator
— Input: linkerCommandFileID of type String - Handle to a linkerCommandFile element
— Input: generatorRef of type String - The value of the generatorRef element

#### F.7.45.47 getLinkerCommandFileGeneratorRefByNames

Description: Returns all the generatorRefs defined on the given linkerCommandFile element.

— Returns: generatorRefs of type String - List of the referenced generators
— Input: linkerCommandFileID of type String - Handle to a linkerCommandFile element

#### F.7.45.48 getLinkerCommandFileGeneratorRefIDs

Description: Returns the handles to all the generatorRefs defined on the given linkerCommandFile element.

— Returns: generatorRefIDs of type String - List of handles to the generatorRef elements

— Input: linkerCommandFileID of type String - Handle to a linkerCommandFile element

#### F.7.45.49 getLinkerCommandFileLineSwitch

Description: Returns the commandLineSwitch value defined on the given linkerCommandFile element.

— Returns: value of type String - The commandLineSwitch value
— Input: linkerCommandFileID of type String - Handle to a linkerCommandFile element

#### F.7.45.50 getLinkerCommandFileLineSwitchExpression

Description: Returns the commandLineSwitch expression defined on the given linkerCommandFile.

— Returns: valueExpression of type String - The commandLineSwitch expression
— Input: linkerCommandFileID of type String - Handle to a linkerCommandFile

#### F.7.45.51 getLinkerCommandFileName

Description: Returns the fileName defined on the given linkerCommandFile element.

— Returns: fileName of type String - The file name
— Input: linkerCommandFileID of type String - Handle to a linkerCommandFile element

#### F.7.45.52 getLinkerCommandFileNameExpression

Description: Returns the fileName expression defined on the given linkerCommandFile.

— Returns: fileNameExpression of type String - The fileName expression
— Input: linkerCommandFileID of type String - Handle to a linkerCommandFile

#### F.7.45.53 getLinkerCommandFileNameID

Description: Returns the handle to the name defined on the given linkerCommandFile element.

— Returns: nameID of type String - Handle to the name element
— Input: linkerCommandFileID of type String - Handle to a linkerCommandFile element

#### F.7.45.54 getLinkerCommandFileNameValue

Description: Returns the name defined on the given linkerCommandFile element.

— Returns: name of type String - The linkerCommandFile name
— Input: linkerCommandFileID of type String - Handle to a linkerCommandFile element

### F.7.46 File builder (EXTENDED)

#### F.7.46.1 addExecutableImageFileBuilderID

Description: Adds a fileBuilder with the given fileType and command to the given executableImage
element.

— Returns: fileBuilderID of type String - Handle to a new fileBuilder element
— Input: executableImageID of type String - Handle to an executableImage element
— Input: fileType of type String - The fileBuilder fileType
— Input: command of type String - The fileBuilder commands

#### F.7.46.2 addExecutableImageLinkerCommandFile

Description: Adds the given linkerCommandFile name with its switch and enable flags to the given
executableImage element.

— Returns: linkerCommandFileID of type String - Handle to a new linkerCommandFile element
— Input: executableImageID of type String - Handle to an executableImage element
— Input: name of type String - ExecutableImage linkerCommandFile
— Input: commandLineSwitch of type String - Flag on the command line specifying the linker

command file

— Input: enable of type Boolean - Indicates whether to use this linker command file in the default

scenario

#### F.7.46.3 addLanguageToolsFileBuilder

Description: Adds a fileBuilder on a languageTools element.

— Returns: fileBuilderID of type String - the fileBuilder identifier added on the languageTools element

— Input: languageToolsID of type String - Handle to a languageTools element
— Input: fileType of type String - The fileBuilder fileType
— Input: command of type String - The fileBuilder commands

#### F.7.46.4 addLinkerCommandFileGeneratorRef

Description: Adds a generatorRef on a linkerCommandFile element.

— Returns: generatorRefID of type String - the generatorRef identifier
— Input: linkerCommandFileID of type String - Handle to a linkerCommandFile element
— Input: generatorRef of type String - The generatorRef to be added

#### F.7.46.5 removeBuildCommandCommand

Description: Removes a command with from the a build command element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: buildCommandID of type String - Handle to a buildCommand element

#### F.7.46.6 removeBuildCommandFlags

Description: Removes buildCommandFlags from the given file element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileID of type String - Handle to a file element

#### F.7.46.7 removeBuildCommandReplaceDefaultFlags

Description: Removes ReplaceDefaultFlags from the given buildCommand element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: buildCommandID of type String - Handle to a buildCommand element

#### F.7.46.8 removeBuildCommandTargetName

Description: Removes buildCommandReplaceDefaultFlags from the given file element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileID of type String - Handle to a file element

#### F.7.46.9 removeDefaultFileBuilderCommand

Description: Removes command from the given defaultFileBuilder element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: defaultFileBuilderID of type String - Handle to a defaultFileBuilder element

#### F.7.46.10 removeExecutableImageFileBuilderID

Description: Removes the given fileBuilder element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileBuilderID of type String - Handle to a fileBuilder element

#### F.7.46.11 removeExecutableImageLanguageTools

Description: Removes the languageTools structure on an executableImage element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: executableImageID of type String - Handle to an executableImage element

#### F.7.46.12 removeExecutableImageLinkerCommandFile

Description: Removes the given linkerCommandFile element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: linkerCommandFileID of type String - Handle to a linkerCommandFile

#### F.7.46.13 removeFileBuilderCommand

Description: Removes command from the given fileBuilder element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileBuilderID of type String - Handle to a fileBuilder element

#### F.7.46.14 removeFileBuilderFlags

Description: Removes flags from the given fileBuilder element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileBuilderID of type String - Handle to a fileBuilder element

#### F.7.46.15 removeFileBuilderReplaceDefaultFlags

Description: Removes replaceDefaultFlags with the given value for the given fileBuilder element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileBuilderID of type String - Handle to a fileBuilder element

#### F.7.46.16 removeLanguageToolsFileBuilder

Description: Removes the given fileBuilder from its languageTools element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)

— Input: fileBuilderID of type String - Handle to a fileBuilder element

#### F.7.46.17 removeLanguageToolsLinkerCommandFile

Description: Removes the linkerCommandFile structure on a languageTools element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: languageToolsID of type String - Handle to a languageTools element

#### F.7.46.18 removeLanguageToolsLinkerFlags

Description: Removes the linkerFlag structure on a languageTools element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: languageToolsID of type String - Handle to a languageTools element

#### F.7.46.19 removeLinkerCommandFileGeneratorRef

Description: Removes the given generatorRef from its containing linkerCommandFile element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: generatorRefID of type String - Handle of a generateRef element

#### F.7.46.20 setBuildCommandCommand

Description: Sets command with the given value for the given buildCommand element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: buildCommandID of type String - Handle to a buildCommand element
— Input: command of type String - File buildCommand command expression

#### F.7.46.21 setBuildCommandFlags

Description: Sets buildCommandFlags with the given value for the given file element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: buildCommandID of type String - Handle to a file element
— Input: flags of type String - File buildCommand flags

#### F.7.46.22 setBuildCommandReplaceDefaultFlags

Description: Sets ReplaceDefaultFlags with the given value for the given buildCommand element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: buildCommandID of type String - Handle to a buildCommand element
— Input: valueExpression of type String - File buildCommand replace default flags

#### F.7.46.23 setBuildCommandTargetName

Description: Sets buildCommandReplaceDefaultFlags with the given value for the given file element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: buildCommandID of type String - Handle to a file element
— Input: targetName of type String - File buildCommand target name

#### F.7.46.24 setExecutableImageLanguageTools

Description: Sets the languageTools structure on an executableImage element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: executableImageID of type String - Handle to an executableImage element

#### F.7.46.25 setExecutableImageLinker

Description: Sets the linker with the given value for the given executableImage element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: executableImageID of type String - Handle to an executableImage element
— Input: linker of type String - The executableImage linker

#### F.7.46.26 setExecutableImageLinkerFlags

Description: Sets the linkerFlags with the given value for the given executableImage element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: executableImageID of type String - Handle to an executableImage element
— Input: linkerFlags of type String - The executableImage linkerFlags

#### F.7.46.27 setFileBuildCommand

Description: Sets buildCommand with the given value for the given file element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileID of type String - Handle to a file element

#### F.7.46.28 setFileBuilderCommand

Description: Sets command with the given value for the given fileBuilder element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileBuilderID of type String - Handle to a fileBuilder element
— Input: command of type String - The fileBuilder command

#### F.7.46.29 setFileBuilderFileType

Description: Sets fileType with the given value for the given fileBuilder element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileBuilderID of type String - Handle to a fileBuilder element
— Input: fileTypeValue of type String - The fileTypeValue

#### F.7.46.30 setFileBuilderFlags

Description: Sets flags with the given value for the given fileBuilder element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileBuilderID of type String - Handle to a fileBuilder element
— Input: flags of type String - The fileBuilder flags

#### F.7.46.31 setFileBuilderReplaceDefaultFlags

Description: Sets replaceDefaultFlags with the given value for the given fileBuilder element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileBuilderID of type String - Handle to a fileBuilder element
— Input: valueExpression of type String - The fileBuilder replace default flags

#### F.7.46.32 setLanguageToolsLinker

Description: Sets the linker stringExpression on a languageTools element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: languageToolsID of type String - Handle to a languageTools element
— Input: linker of type String - The linker expression to set

#### F.7.46.33 setLanguageToolsLinkerCommandFile

Description: Sets the linkerCommandFile structure on a languageTools element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: languageToolsID of type String - Handle to a languageTools element
— Input: name of type String - The name expression to set
— Input: commandLineSwitch of type String - The commandLineSwitch expression to set
— Input: enable of type String - The enable expression to set
— Input: linker of type String - The linker expression to set

#### F.7.46.34 setLanguageToolsLinkerFlags

Description: Sets the linkerFlags stringExpression on a languageTools element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: languageToolsID of type String - Handle to a languageTools element
— Input: linkerFlags of type String - The linkerFlags expression to set
— Input: linker of type String - The linker expression to set

#### F.7.46.35 setLinkerCommandFileCommandLineSwitch

Description: Sets the commandLineSwitch expression on a linkerCommandFile element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: linkerCommandFileID of type String - Handle to a linkerCommandFile element
— Input: commandLineSwitch of type String - the commandLineSwitch expression to set

#### F.7.46.36 setLinkerCommandFileEnable

Description: Sets the enable expression on a linkerCommandFile element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: linkerCommandFileID of type String - Handle to a linkerCommandFile element
— Input: enable of type String - the enable expression to set

#### F.7.46.37 setLinkerCommandFileName

Description: Sets the name of the linkerCommandFile element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: linkerCommandFileID of type String - Handle to a linkerCommandFile element
— Input: name of type String - File name

### F.7.47 File set (BASE)

#### F.7.47.1 getBuildCommandReplaceDefaultFlagsExpression

Description: Returns the replaceDefaultFlags expression defined on the given buildCommand element.

— Returns: flagsExpression of type String - The buildCommands replaceDefaultFlags

expression

— Input: buildCommandID of type String - Handle to a buildCommand element

#### F.7.47.2 getFileDefineIDs

Description: Returns the handles to all the fileDefines defined on the given file element.

— Returns: fileDefineIDs of type String - List of handles to the fileDefine elements
— Input: fileID of type String - Handle to a file element

#### F.7.47.3 getFileDefineSymbolValue

Description: Returns the value defined on the given fileDefine element.

— Returns: value of type String - The file define value
— Input: fileDefineID of type String - Handle to a fileDefine element

#### F.7.47.4 getFileDependencyIDs

Description: Returns the handles to all the dependency elements defined on the given file element.

— Returns: dependencyIDs of type String - List of handles to the dependency elements
— Input: fileID of type String - Handle to a file element

#### F.7.47.5 getFileExportedNameIDs

Description: Returns the handles to all the exportedNames defined on the given file element.

— Returns: exportedNameIDs of type String - List of handles to the exportedName elements
— Input: fileID of type String - Handle to a file element

#### F.7.47.6 getFileExportedNames

Description: Returns the exportedNames defined on the given file element.

— Returns: exportedNames of type String - List of exported names
— Input: fileID of type String - Handle to a file element

#### F.7.47.7 getFileFileTypeIDs

Description: Returns the handles to all the fileTypes defined on the given file element.

— Returns: fileTypeID of type String - List of handles to the fileType elements
— Input: fileID of type String - Handle to a file element

#### F.7.47.8 getFileFileTypes

Description: Returns the fileTypes defined on the given file element.

— Returns: fileTypes of type String - List of file types
— Input: fileID of type String - Handle to a file element

#### F.7.47.9 getFileImageTypeIDs

Description: Returns the handles to all the imageTypes defined on the given file element.

— Returns: imageTypeIDs of type String - List of handles to the imageType elements
— Input: fileID of type String - Handle to a file element

#### F.7.47.10 getFileImageTypes

Description: Returns all the imageTypes defined on the given file element.

— Returns: imageTypes of type String - List of image types
— Input: fileID of type String - Handle to a file element

#### F.7.47.11 getFileIsIncludeFile

Description: Returns the isIncludeFile element defined on the given file element.

— Returns: value of type Boolean - The isIncludeFile value
— Input: fileID of type String - Handle to a file element

#### F.7.47.12 getFileIsIncludeFileID

Description: Returns the handle to the isIncludeFile defined on the given file element.

— Returns: isIncludeFileID of type String - Handle to the isIncludeFile element
— Input: fileID of type String - Handle to a file element

#### F.7.47.13 getFileIsStructural

Description: Returns the isStructural element defined on the given file element.

— Returns: value of type Boolean - File isStructural value
— Input: fileID of type String - Handle to a file element

#### F.7.47.14 getFileLogicalName

Description: Returns the logicalName defined on the given file element.

— Returns: logicalName of type String - The logical name
— Input: fileID of type String - Handle to a file element

#### F.7.47.15 getFileLogicalNameID

Description: Returns the handle to the logicalName defined on the given file element.

— Returns: logicalNameID of type String - Handle to the logicalName element

— Input: fileID of type String - Handle to a file element

#### F.7.47.16 getFileName

Description: Returns the name defined on the given file element.

— Returns: name of type String - The file name
— Input: fileID of type String - Handle to a file element

#### F.7.47.17 getFileSetDefaultFileBuilderIDs

Description: Returns the handles to all the fileBuilders defined on the given fileSet element.

— Returns: fileBuilderIDs of type String - List of handles to the fileBuilder elements
— Input: fileSetID of type String - Handle to a fileSet element

#### F.7.47.18 getFileSetDependencyIDs

Description: Returns the handles to all the dependency elements defined on the given fileSet element.

— Returns: dependencyIDs of type String - List of handles to the fileSet elements
— Input: fileSetID of type String - Handle to a fileSet element

#### F.7.47.19 getFileSetFileIDs

Description: Returns the handles to all the files defined on the given fileSet element.

— Returns: fileIDs of type String - List of handles to file elements
— Input: fileSetID of type String - Handle to a fileSet element

#### F.7.47.20 getFileSetFunctionIDs

Description: Returns the handles to all the functions defined on the given fileSet element.

— Returns: functionIDs of type String - List of handles to the function elements
— Input: fileSetID of type String - Handle to a fileSet element

#### F.7.47.21 getFileSetGroupFileSetRefIDs

Description: Returns the handles to all the fileSetRefs defined on the given fileSetGroup element.

— Returns: fileSetRefIDs of type String - List of handles to the fileSetRef elements
— Input: fileSetRefGroupID of type String - Handle to a fileSetRefGroup element

#### F.7.47.22 getFileSetGroupIDs

Description: Returns the handles to all the groups defined on the given fileSet element.

— Returns: groupID of type String - List of handles to the group elements
— Input: fileSetID of type String - Handle to a fileSet element

#### F.7.47.23 getFileSetGroups

Description: Returns all the groups defined on the given fileSet element.

— Returns: groups of type String - List of fileSet groups
— Input: fileSetID of type String - Handle to a fileSet element

#### F.7.47.24 getFileSetRefByID

Description: Returns the handle to the fileSet referenced from the given fileSetRef element.

— Returns: fileSetRefID of type String - Handle to the referenced fileSet element
— Input: fileSetRefID of type String - Handle to a fileSetRef element

#### F.7.47.25 getFileSetRefGroupFileSetRefIDs

Description: Returns the handles to all the fileSetRefs defined on the given fileSetRefGroup element.

— Returns: fileSetRefIDs of type String - List of handles to the fileSetRef elements
— Input: fileSetRefGroupID of type String - Handle to a fileSetRefGroup

#### F.7.47.26 getFileSetRefLocalNameRefByID

Description: Returns the handle to the fileSet referenced from the given fileSetRef element.

— Returns: fileSetID of type String - Handle to the referenced fileSet element
— Input: fileSetRefID of type String - Handle to a fileSetRef element

#### F.7.47.27 getFunctionArgumentDataType

Description: Returns the dataType defined on the given argument element.

— Returns: dataType of type String - The argument data type
— Input: argumentID of type String - Handle to an argument element

#### F.7.47.28 getFunctionArgumentIDs

Description: Returns the handles to all the arguments defined on the given function element.

— Returns: argumentIDs of type String - List of handles to argument elements
— Input: functionID of type String - Handle to a function element

#### F.7.47.29 getFunctionDisabled

Description: Returns the disabled element defined on the given function element.

— Returns: value of type Boolean - True if the function is disabled
— Input: functionID of type String - Handle to a function element

#### F.7.47.30 getFunctionDisabledExpression

Description: Returns the disabled expression defined on the given function element.

— Returns: valueExpression of type String - The disabled expression
— Input: functionID of type String - Handle to a function element

#### F.7.47.31 getFunctionDisabledID

Description: Returns the handle to the disabled element defined on the given fileSet function element.

— Returns: DisabledID of type String - Handle to the disabled element
— Input: functionID of type String - Handle to a function element

#### F.7.47.32 getFunctionEntryPoint

Description: Returns the entryPoint defined on the given function element.

— Returns: entryPoint of type String - The function entry point
— Input: functionID of type String - Handle to a function element

#### F.7.47.33 getFunctionFileID

Description: Returns the handle to the file defined on the given function element.

— Returns: fileID of type String - Handle to the file element
— Input: functionID of type String - Handle to a function element

#### F.7.47.34 getFunctionFileRefByID

Description: Returns the fileID defined on the given function element.

— Returns: fileID of type String - Handle to the referenced file element
— Input: functionID of type String - Handle to a function element

#### F.7.47.35 getFunctionFileRefByName

Description: Returns the fileRef defined on the given function element.

— Returns: fileRef of type String - The referenced file
— Input: functionID of type String - Handle to a function element

#### F.7.47.36 getFunctionReplicate

Description: Returns the replicate element defined on the given function element.

— Returns: replicate of type Boolean - The replicate value
— Input: functionID of type String - Handle to a function element

#### F.7.47.37 getFunctionReturnType

Description: Returns the returnType defined on the given function element.

— Returns: returnType of type String - The function return type
— Input: functionID of type String - Handle to a function element

#### F.7.47.38 getFunctionSourceFileIDs

Description: Returns the handles to all the sourceFiles defined on the given function element.

— Returns: functionSourceFileIDs of type String - List of handles to sourceFile elements
— Input: functionID of type String - Handle to a function element

#### F.7.47.39 getFunctionSourceFileName

Description: Returns the name defined on the given function sourceFile element.

— Returns: name of type String - The SourceFile name
— Input: functionSourceFileID of type String - Handle to a functionSourceFile element

#### F.7.47.40 getFunctionSourceFileType

Description: Returns the fileType element defined on the given functionSourceFile element.

— Returns: type of type String - The fileType value
— Input: functionSourceFileID of type String - Handle to a functionSourceFile element

#### F.7.47.41 getSourceFileFileType

Description: Returns the fileType value defined on the given sourceFile element.

— Returns: fileType of type String - The fileType value
— Input: sourceFileID of type String - Handle to a sourceFile element

#### F.7.47.42 getSourceFileFileTypeID

Description: Returns the handle to the fileType defined on the given sourceFile element.

— Returns: fileTypeID of type String - Handle to the fileType element
— Input: sourceFileID of type String - Handle to a sourceFile element

#### F.7.47.43 getSourceFileSourceName

Description: Returns the sourceName defined on the given sourceFile element.

— Returns: sourceName of type String - The sourceName value
— Input: sourceFileID of type String - Handle to a sourceFile element

### F.7.48 File set (EXTENDED)

#### F.7.48.1 addFileDefine

Description: Adds fileDefine with the given name and value to the given file element.

— Returns: fileDefineID of type String - Handle to a new fileDefine
— Input: fileID of type String - Handle to a file element
— Input: name of type String - FileDefine name
— Input: value of type String - FileDefine value

#### F.7.48.2 addFileDependency

Description: Adds given dependency to the given file element.

— Returns: dependencyID of type String - Handle to a new Dependency
— Input: fileID of type String - Handle to a file element
— Input: dependency of type String - File dependency

#### F.7.48.3 addFileExportedName

Description: Adds an exportedName on a file element.

— Returns: exportedNameID of type String - the exportedName identifier
— Input: fileID of type String - Handle to a file element
— Input: value of type String - The value of the exported Name

#### F.7.48.4 addFileFileType

Description: Adds a fileType on a file element.

— Returns: fileTypeID of type String - The fileType identifier on the file element
— Input: fileID of type String - Handle of a file element
— Input: fileType of type String - The fileType value to be added

#### F.7.48.5 addFileImageType

Description: Adds an imageType on a file element.

— Returns: imageTypeID of type String - The imageType identifier
— Input: fileID of type String - Handle to a file element
— Input: value of type String - The value of the image type

#### F.7.48.6 addFileSetDefaultFileBuilder

Description: Adds defaultFileBuilder with the given fileType to the given file element.

— Returns: fileBuilderID of type String - Handle to a new fileBuilder
— Input: fileID of type String - Handle to a file element
— Input: fileType of type String - The defaultFileBuilder fileType

#### F.7.48.7 addFileSetDependency

Description: Adds given dependency to the given fileSet element.

— Returns: dependencyID of type String - Handle to a new dependency
— Input: fileSetID of type String - Handle to a fileSet element
— Input: dependency of type String - The fileSet dependency

#### F.7.48.8 addFileSetFile

Description: Adds file with the given name and fileTypes to the given fileSet element.

— Returns: fileID of type String - Handle to a new file
— Input: fileSetID of type String - Handle to a fileSet element
— Input: name of type String - File name
— Input: fileTypes of type String[] - File fileTypes

#### F.7.48.9 addFileSetFunction

Description: Adds function with the given fileRef to the given fileSet element.

— Returns: functionID of type String - Handle to a new function
— Input: fileSetID of type String - Handle to a fileSet element
— Input: fileRef of type String - Reference to the file that contains the entry point for the function

#### F.7.48.10 addFileSetGroup

Description: Adds a group element on the given fileSet.

— Returns: groupID of type String - The group identifier
— Input: fileSetID of type String - Handle of a fileSet element

— Input: group of type String - the value to set on the Group

#### F.7.48.11 addFileSetRefGroupFileSetRef

Description: Adds a fileSet reference (a local file name) to a fileSetRefGroup.

— Returns: fileSetRefID of type String - The identifier of the added fileSetRef
— Input: fileSetRefGroupID of type String - Handle to the fileSetRefGroup
— Input: localName of type String - Name of a fileSet

#### F.7.48.12 addFunctionArgument

Description: Adds argument with given name and value to the given function element.

— Returns: argumentID of type String - Handle to a new argument
— Input: functionID of type String - Handle to a function element
— Input: name of type String - Argument name
— Input: value of type String - Argument value
— Input: dataType of type String - Argument dataType

#### F.7.48.13 addFunctionSourceFile

Description: Adds sourceFile with the given sourceName and fileType to the given function element.

— Returns: functionSourceFileID of type String - Handle to a new sourceFile
— Input: functionID of type String - Handle to a function element
— Input: sourceFileName of type String - Source file name
— Input: fileType of type String - Source file type

#### F.7.48.14 removeFileBuildCommand

Description: Removes the buildCommand from its containing file element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileID of type String - Handle to a file element

#### F.7.48.15 removeFileDefine

Description: Removes the given fileDefine element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: defineID of type String - Handle to a define element

#### F.7.48.16 removeFileDependency

Description: Removes given dependency to the given file element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: depedencyID of type String - File dependency

#### F.7.48.17 removeFileExportedName

Description: Removes the exported name from its containing file element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: exportedNameID of type String - Handle to an exportedName element

#### F.7.48.18 removeFileFileType

Description: Removes the given fileType from its containing file element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileTypeID of type String - Handle to a fileType element

#### F.7.48.19 removeFileImageType

Description: Removes the given imageType from its containing file element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: imageTypeID of type String - Handle to an imageType element

#### F.7.48.20 removeFileIsIncludeFile

Description: Removes isIncludeFile from the given file element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileID of type String - Handle to a file element

#### F.7.48.21 removeFileIsStructural

Description: Removes isStructural from the given file element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileID of type String - Handle to a file element

#### F.7.48.22 removeFileLogicalName

Description: Removes logicalName from the given file element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileID of type String - Handle to a file element

#### F.7.48.23 removeFileSetDefaultFileBuilder

Description: Removes the given defaultFileBuilder element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileBuilderID of type String - Handle to a fileBuilder element

#### F.7.48.24 removeFileSetDependency

Description: Removes the given dependency from its parent.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: dependencyID of type String - Handle to a dependency element

#### F.7.48.25 removeFileSetFile

Description: Removes the given file.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileID of type String - Handle to a file element

#### F.7.48.26 removeFileSetFunction

Description: Removes the given function element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: functionID of type String - Handle to a function element

#### F.7.48.27 removeFileSetGroup

Description: Removes the given group from its containing fileSet element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: groupID of type String - Handle of a group element

#### F.7.48.28 removeFunctionArgument

Description: Removes the given argument.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: argumentID of type String - Handle to an argument element

#### F.7.48.29 removeFunctionDisabled

Description: Removes disabled from the given function element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: functionID of type String - Handle to a function element

#### F.7.48.30 removeFunctionEntryPoint

Description: Removes entryPoint from the given function element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: functionID of type String - Handle to a function element

#### F.7.48.31 removeFunctionReturnType

Description: Removes returnType from the given function element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: functionID of type String - Handle to a function element

#### F.7.48.32 removeFunctionSourceFile

Description: Removes the given sourceFile element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: functionSourceFileID of type String - Handle to a functionSourceFile element

#### F.7.48.33 setFileIsIncludeFile

Description: Sets isIncludeFile with the given value for the given file element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileID of type String - Handle to a file element
— Input: value of type Boolean - File inIncludeFile value

#### F.7.48.34 setFileIsStructural

Description: Sets isStructural with the given value for the given file element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileID of type String - Handle to a file element
— Input: value of type Boolean - File isStructural value

#### F.7.48.35 setFileLogicalName

Description: Sets logicalName with the given value for the given file element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileID of type String - Handle to a file element
— Input: logicalName of type String - File logicalName value

#### F.7.48.36 setFileName

Description: Sets the name expression on a file element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileID of type String - Handle to a file element
— Input: name of type String -Name expression

#### F.7.48.37 setFunctionArgumentDataType

Description: Sets datatype with the given type for the given argument element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: argumentID of type String - Handle to an argument element
— Input: dataType of type String - Argument dataType

#### F.7.48.38 setFunctionDisabled

Description: Sets disabled to the given value for the given function element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: functionID of type String - Handle to a function element
— Input: disabledExpression of type String - Function disabled

#### F.7.48.39 setFunctionEntryPoint

Description: Sets entryPoint to the given value for the given function element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: functionID of type String - Handle to a function element
— Input: entryPoint of type String - Function entryPoint

#### F.7.48.40 setFunctionFileRef

Description: Sets the fileRef value for the given function element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: functionID of type String - Handle to a function element
— Input: fileRef of type String - fileRef value

#### F.7.48.41 setFunctionReplicate

Description: Sets replicate to the given value for the given function element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: functionID of type String - Handle to a function element
— Input: replicate of type Boolean - Function replicate

#### F.7.48.42 setFunctionReturnType

Description: Sets returnType to the given value for the given function element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: functionID of type String - Handle to a function element
— Input: returnType of type String - Function returnType

#### F.7.48.43 setFunctionSourceFileName

Description: Sets sourceFileName with the given value for the given function element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: functionID of type String - Handle to a function element
— Input: value of type String - sourceFile name

#### F.7.48.44 setSourceFileFileType

Description: Sets the fileType on a sourceFile element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: sourceFileID of type String - Handle to a sourceFile element
— Input: value of type String - Value of the fileType to set

#### F.7.48.45 setSourceFileSourceName

Description: Sets the sourceName on a sourceFile element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: sourceFileID of type String - Handle to a sourceFile element
— Input: sourceName of type String - Value of sourceName to set

### F.7.49 Generator (BASE)

#### F.7.49.1 getAbstractorGeneratorGroup

Description: Returns the group names defined on the given abstractorGenerator element.

— Returns: groups of type String - The group names
— Input: abstractorGeneratorID of type String - Handle to an abstractorGenerator element

#### F.7.49.2 getAbstractorGeneratorGroupIDs

Description: Returns the handles to all the groups defined on the given abstractorGenerator element.

— Returns: groupIDs of type String - List of handles to the group elements
— Input: abstractorGeneratorID of type String - Handle to an abstractorGenerator element

#### F.7.49.3 getComponentGeneratorGroupIDs

Description: Returns the handles to all the groups defined on the given component generator element.

— Returns: groupIDs of type String - List of handles to the group elements
— Input: componentGeneratorID of type String - Handle to a componentGenerator element

#### F.7.49.4 getGeneratorApiService

Description: Returns the apiService defined on the given generator element.

— Returns: apiService of type String - The apiService value
— Input: generatorID of type String - Handle to a generator element

#### F.7.49.5 getGeneratorApiTypeID

Description: Returns the handle to the apiType defined on the given generator element.

— Returns: apiTypeID of type String - Handle to the apiType element
— Input: generatorID of type String - Handle to a generator element

#### F.7.49.6 getGeneratorExecutable

Description: Returns the executable defined on the given generator element.

— Returns: executable of type String - The generator executable file
— Input: generatorID of type String - Handle to a generator element

#### F.7.49.7 getGeneratorGeneratorExe

Description: Returns the generatorExe value defined on the given generator element

— Returns: generatorExe of type String - The generatorExe value
— Input: generatorID of type String - Handle to a generator element

#### F.7.49.8 getGeneratorGroups

Description: Returns all the groups defined on the given generator element.

— Returns: groups of type String - List of generator groups
— Input: generatorID of type String - Handle to a generator element

#### F.7.49.9 getGeneratorPhase

Description: Returns the phase defined on the given generator element.

— Returns: phase of type Double - The phase number
— Input: generatorID of type String - Handle to a generator element

#### F.7.49.10 getGeneratorPhaseExpression

Description: Returns the phase defined on the given generator element.

— Returns: phaseExpression of type String - The generator phase
— Input: generatorID of type String - Handle to a generator element

#### F.7.49.11 getGeneratorPhaseID

Description: Returns the handle to the phase defined on the given generator element.

— Returns: phaseID of type String - Handle to the phase element
— Input: generatorID of type String - Handle to a generator element

#### F.7.49.12 getGeneratorScope

Description: Returns the scope defined on the given generator element.

— Returns: scope of type String - The generator scope
— Input: generatorID of type String - Handle to a generator element

#### F.7.49.13 getGeneratorTransportMethodsID

Description: Returns the handle to the transportMethods defined on the given generator element.

— Returns: transportMethodsID of type String - Handle to the transportMethods element
— Input: generatorID of type String - Handle to a generator element

#### F.7.49.14 getTransportMethodsTransportMethodID

Description: Returns the handle to the transportMethod defined on the given transportMethods element.

— Returns: transportMethodID of type String - Handle to the transportMethod element
— Input: transportMethodsID of type String - Handle to a transportMethods element

### F.7.50 Generator (EXTENDED)

#### F.7.50.1 addAbstractorGeneratorGroup

Description: Adds a group on an abstractorGenerator element.

— Returns: groupID of type String - the group identifier
— Input: abstractorGeneratorID of type String - Handle to an abstractorGenerator element
— Input: value of type String - the value of the added group

#### F.7.50.2 addComponentGeneratorGroup

Description: Adds a group to a componentGenerator element.

— Returns: groupID of type String - the group identifier
— Input: componentGeneratorID of type String - Handle to a componentGenerator element
— Input: value of type String - value to set on the group

#### F.7.50.3 removeAbstractorGeneratorGroup

Description: Removes the given group from the abstractor generator element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: groupID of type String - Handle to a group element

#### F.7.50.4 removeComponentGeneratorGroup

Description: Removes the given group from its containing component generator element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: groupID of type String - Handle to a group element

#### F.7.50.5 removeGeneratorApiService

Description: Removes apiService from the given generator.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: generatorID of type String - Handle to a generator

#### F.7.50.6 removeGeneratorApiType

Description: Removes apiType from the given generator.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: generatorID of type String - Handle to a generator

#### F.7.50.7 removeGeneratorPhase

Description: Removes phase with the given value for the given generator element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: generatorID of type String - Handle to a generator element

#### F.7.50.8 removeGeneratorTransportMethods

Description: Removes transportMethods from the given generator.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: generatorID of type String - Handle to a generator

#### F.7.50.9 removeTransportMethodsTransportMethod

Description: Removes the transportMethod identifier on a transportMethods element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: transportMethodsID of type String - Handle to a transportMethods element

#### F.7.50.10 setGeneratorApiService

Description: Sets apiService with the given value for the given generator element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: generatorID of type String - Handle to a generator element
— Input: apiService of type String - Generator apiService

#### F.7.50.11 setGeneratorApiType

Description: Sets apiType with the given value for the given generator | componentGenerator |
abstractorGenerator element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: generatorID of type String - Handle to a generator | componentGenerator | abstractor-

Generator element

— Input: apiType of type String - Generator apiType

#### F.7.50.12 setGeneratorGeneratorExe

Description: Sets the generatorExe value on a generator element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: generatorID of type String - Handle to a generator element
— Input: generatorExe of type String - the value of the generatorExe

#### F.7.50.13 setGeneratorPhase

Description: Sets phase with the given value for the given generator element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: generatorID of type String - Handle to a generator element
— Input: phaseExpression of type String - Generator phase

#### F.7.50.14 setGeneratorScope

Description: Sets scope with the given value for the given generator element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: generatorID of type String - Handle to a generator element
— Input: scope of type String - Generator scope

#### F.7.50.15 setGeneratorTransportMethods

Description: Sets transportMethods with the given value for the given generator element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: generatorID of type String - Handle to a generator element
— Input: transportMethod of type String - Generator transportMethod

#### F.7.50.16 setTransportMethodsTransportMethod

Description: Set the transportMethod on a transportMethods element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: transportMethodsID of type String - Handle to a transportMethods element
— Input: transportMethod of type String - the transportMethod value

### F.7.51 Generator chain (BASE)

#### F.7.51.1 getComponentGeneratorSelectorGroupSelectorID

Description: Returns the handle to the groupSelector defined on the given componentGeneratorSelector
element.

— Returns: groupSelectorID of type String - Handle to a groupSelector element
— Input: componentGeneratorSelectorID of type String - Handle to a

componentGeneratorSelector element

#### F.7.51.2 getGeneratorChainChainGroupIDs

Description: Returns the handles to all the groups defined on the given generatorChain element.

— Returns: groupIDs of type String - List of handles to the group elements

— Input: generatorChainID of type String - Handle to a generatorChain element

#### F.7.51.3 getGeneratorChainChoiceIDs

Description: Returns the handles to all the choices defined on the given generatorChain object.

— Returns: choiceIDs of type String - List of handles to choice element
— Input: generatorChainID of type String - Handle to a generatorChain element

#### F.7.51.4 getGeneratorChainComponentGeneratorSelectorIDs

Description: Returns the handles to all the componentGeneratorSelectors defined on the given
generatorChain element.

— Returns: componentGeneratorSelectorIDs of type String - List of handles from the

componentGeneratorSelector elements

— Input: generatorChainID of type String - Handle to a generatorChain element

#### F.7.51.5 getGeneratorChainGeneratorChainSelectorIDs

Description: Returns the handles to all the generatorChainSelectors defined on the given generatorChain
element.

— Returns: generatorChainSelectorIDs of type String - List of handles to the

generatorChainSelector elements

— Input: generatorChainID of type String - Handle to a generatorChain element

#### F.7.51.6 getGeneratorChainGeneratorIDs

Description: Returns the handles to all the generators defined on the given generatorChain object.

— Returns: generatorIDs of type String - List of handles to generator elements
— Input: generatorChainID of type String - Handle to a generatorChain object

#### F.7.51.7 getGeneratorChainSelectorGeneratorChainRefByID

Description: Returns
generatorChainSelector element.

the handle

to

the generatorChain

instance

referenced

from

the given

— Returns: generatorChainID of type String - Handle to the referenced generatorChain object
— Input: generatorChainSelectorID of type String - Handle to a generatorChainSelector element

#### F.7.51.8 getGeneratorChainSelectorGeneratorChainRefByVLNV

Description: Returns the VLNV of the generatorChain referenced from the given generatorChainSelector
element.

— Returns: VLNV of type String - The VLNV of the referenced generatorChain object
— Input: generatorChainSelectorID of type String - Handle to a generatorChainSelector element

#### F.7.51.9 getGeneratorChainSelectorGroupSelectorID

Description: Returns the handle to the groupSelector defined on the given generatorChainSelector element.

— Returns: groupSelectorID of type String - Handle to the groupSelector element

— Input: generatorChainSelectorID of type String - Handle to a generatorChainSelector element

#### F.7.51.10 getGroupSelectorNameIDs

Description: Returns the handles to all names defined on the given groupSelector element.

— Returns: nameIDs of type String - List of handles to the name elements
— Input: groupSelectorID of type String - Handle to a groupSelector element

#### F.7.51.11 getGroupSelectorSelectionNames

Description: Returns names for a given groupSelector element.

— Returns: names of type String - List of generator(chain) group names
— Input: groupSelectorID of type String - Handle to a groupSelector element

#### F.7.51.12 getGroupSelectorSelectionOperator

Description: Returns multipleGroupSelectionOperation for a given groupSelector element.

— Returns: operator of type String - Operator expression
— Input: groupSelectorID of type String - Handle to a groupSelector element

### F.7.52 Generator chain (EXTENDED)

#### F.7.52.1 addGeneratorChainChainGroup

Description: Adds chainGroup with the given value to the given generatorChain element.

— Returns: status of type String - Indicates call is successful (true) or not (false)
— Input: generatorChainID of type String - Handle to a generatorChain element
— Input: group of type String - ChainGroup value

#### F.7.52.2 addGeneratorChainChoice

Description: Adds choice with the given name and enumerations to the given generatorChain element.

— Returns: choiceID of type String - Handle to a choice element
— Input: generatorChainID of type String - Handle to a generatorChain element
— Input: name of type String - Choice name
— Input: enumerations of type String[] - Choice enumeration values

#### F.7.52.3 addGeneratorChainComponentGeneratorSelector

Description: Adds an componentGeneratorSelector to the given generatorChain element.

— Returns: componentGeneratorSelectorID of type String - Handle to a new

componentGeneratorSelector element

— Input: generatorChainID of type String - Handle to a generatorChain element
— Input: name of type String - groupSelector name

#### F.7.52.4 addGeneratorChainGenerator

Description: Adds generator with the given generatorExe to the given generatorChain element.

— Returns: generatorID of type String - Handle to a generator element
— Input: generatorChainID of type String - Handle to a generatorChain element
— Input: name of type String - name of the generator
— Input: generatorExecutable of type String - Path to generator executable

#### F.7.52.5 addGeneratorChainGeneratorChainSelector

Description: Adds an generatorChainSelector to the given generatorChain element.

— Returns: generatorChainSelectorID of type String - Handle to a new

generatorChainSelector element

— Input: generatorChainID of type String - Handle to a generatorChain element
— Input: name of type String - Name of the new generatorChainSelector

#### F.7.52.6 addGroupSelectorName

Description: Adds an element Name to a group selector element.

— Returns: nameID of type String - Handle of name element
— Input: groupSelectorID of type String - Handle to a groupSelectorName element
— Input: name of type String - Handle the name of the element

#### F.7.52.7 removeGeneratorChainChainGroup

Description: Removes the given chainGroup.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: chainGroupID of type String - Handle to a chainGroup element

#### F.7.52.8 removeGeneratorChainChoice

Description: Removes the given choice element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: choiceID of type String - Handle to a choice element

#### F.7.52.9 removeGeneratorChainComponentGeneratorSelector

Description: Removes an componentGeneratorSelector with the given componentGeneratorSelectorID.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: componentGeneratorSelectorID of type String - Handle to a

componentGeneratorSelector element

#### F.7.52.10 removeGeneratorChainGenerator

Description: Removes a generator with the given generatorID.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: generatorID of type String - Handle to a generator element

#### F.7.52.11 removeGeneratorChainGeneratorChainSelector

Description: Removes a generatorChainSelector with the given generatorChainSelectorID.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)

— Input: generatorChainSelectorID of type String - Handle to a generatorChainSelector element

#### F.7.52.12 removeGroupSelectorName

Description: Removes the given group selector name from its containing element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: groupSelectorNameID of type String - Handle to a groupSelectorName element

#### F.7.52.13 setComponentGeneratorSelectorGroupSelector

Description: Sets the groupSelector with the given value for the given componentGeneratorSelector
element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: componentGeneratorSelectorID of type String - Handle to an

componentGeneratorSelector element

— Input: names of type String[] - groupSelector names

#### F.7.52.14 setGeneratorChainSelectorGeneratorChainRef

Description: Sets the generatorChainRef with the given value for the given generatorChainSelector element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: generatorChainSelectorID of type String - Handle to an generatorChainSelector element

— Input: generatorChainVLNV of type String[] - generatorChain reference

#### F.7.52.15 setGeneratorChainSelectorGroupSelector

Description: Sets the groupSelector with the given value for the given generatorChainSelector element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: generatorChainSelectorID of type String - Handle to an generatorChainSelector element

— Input: names of type String[] - groupSelector names

### F.7.53 Indirect interface (BASE)

#### F.7.53.1 getIndirectAddressRefAddressBlockRefByName

Description: Returns the addressBlockRef defined on the given indirectAddressRef element.

— Returns: addressBlockRef of type String - The referenced addressBlock
— Input: indirectAddressRefID of type String - Handle to an indirectAddressRef element

#### F.7.53.2 getIndirectAddressRefAddressBlockRefID

Description: Returns the handle to the addressBlockRef defined on the given indirectAddressRef element.

— Returns: addressBlockRefID of type String - Handle to the addressBlockRef element
— Input: indirectAddressRefID of type String - Handle to an indirectAddressRef element

#### F.7.53.3 getIndirectAddressRefAddressSpaceRefByName

Description: Returns the addressSpaceRef defined on the given indirectAddressRef element.

— Returns: addressSpaceRef of type String - The referenced addressSpace
— Input: indirectAddressRefID of type String - Handle to an indirectAddressRef element

#### F.7.53.4 getIndirectAddressRefAddressSpaceRefID

Description: Returns the handle to the addressSpaceRef defined on the given indirectAddressRef element.

— Returns: addressSpaceRefID of type String - Handle to the addressSpaceRef element
— Input: indirectAddressRefID of type String - Handle to an indirectAddressRef element

#### F.7.53.5 getIndirectAddressRefAlternateRegisterRefByName

Description: Returns the alternateRegisterRef defined on the given indirectAddressRef element.

— Returns: alternateRegisterRef of type String - The referenced alternateRegister
— Input: indirectAddressRefID of type String - Handle to an indirectAddressRef element

#### F.7.53.6 getIndirectAddressRefAlternateRegisterRefID

Description: Returns the handle to the alternateRegisterRef defined on the given indirectAddressRef
element.

— Returns: alternateRegisterRefID of type String - Handle to the alternateRegisterRef ele-

ment

— Input: indirectAddressRefID of type String - Handle to an indirectAddressRef element

#### F.7.53.7 getIndirectAddressRefBankRefByNames

Description: Returns all the bankRefs defined on the given indirectAddressRef element.

— Returns: bankRefs of type String - List of the referenced banks
— Input: indirectAddressRefID of type String - Handle to an indirectAddressRef element

#### F.7.53.8 getIndirectAddressRefBankRefIDs

Description: Returns the handles to all the bankRefs defined on the given indirectAddressRef element.

— Returns: bankRefIDs of type String - List of handles to the bankRef elements
— Input: indirectAddressRefID of type String - Handle to an indirectAddressRef element

#### F.7.53.9 getIndirectAddressRefFieldRefByName

Description: Returns the FieldRef defined on the given indirectAddressRef element.

— Returns: fieldRef of type String - The referenced field
— Input: indirectAddressRefID of type String - Handle to an indirectAddressRef element

#### F.7.53.10 getIndirectAddressRefFieldRefID

Description: Returns the handle to the fileRef defined on the given indirectAddressRef element.

— Returns: fieldRefID of type String - Handle to the fieldRef element
— Input: indirectAddressRefID of type String - Handle to an indirectAddressRef element

#### F.7.53.11 getIndirectAddressRefMemoryMapRefByName

Description: Returns the memoryMapRef defined on the given indirectAddressRef element.

— Returns: memoryMapRef of type String - The referenced memoryMap
— Input: indirectAddressRefID of type String - Handle to an indirectAddressRef element

#### F.7.53.12 getIndirectAddressRefMemoryMapRefID

Description: Returns the handle to the memoryMapRef defined on the given indirectAddressRef element.

— Returns: memoryMapRefID of type String - Handle to the referenced memoryMapRef element
— Input: indirectAddressRefID of type String - Handle to an indirectAddressRef element

#### F.7.53.13 getIndirectAddressRefMemoryRemapRefByID

Description: Returns the handle to a memoryRemap from the given indirectAddressRef element.

— Returns: memoryRemapID of type String - Handle to a memoryRemap element
— Input: indirectAddressRefID of type String - Handle to a indirectAddressRef element

#### F.7.53.14 getIndirectAddressRefMemoryRemapRefByName

Description: Returns the memoryRemap value from the given indirectAddressRef element.

— Returns: memoryRemapRef of type String - The memoryRemapRef value
— Input: indirectAddressRefID of type String - Handle to a indirectAddressRef element

#### F.7.53.15 getIndirectAddressRefMemoryRemapRefID

Description: Returns the handle to a memoryRemapRef from the given indirectAddressRef element.

— Returns: memoryRemapRefID of type String - Handle to a memoryRemapRef element
— Input: indirectAddressRefID of type String - Handle to a indirectAddressRef element

#### F.7.53.16 getIndirectAddressRefRegisterFileRefByNames

Description: Returns all the registerFiles defined on the given indirectAddressRef element.

— Returns: registerFileRef of type String - List of the referenced registerFiles
— Input: indirectAddressRefID of type String - Handle to an indirectAddressRef element

#### F.7.53.17 getIndirectAddressRefRegisterFileRefIDs

Description: Returns the handles to all the registerFileRefs defined on the given indirectAddressRef
element.

— Returns: registerFileRefIDs of type String - List of handles to the registerFileRef elements
— Input: indirectAddressRefID of type String - Handle to an indirectAddressRef element

#### F.7.53.18 getIndirectAddressRefRegisterRefByName

Description: Returns the RegisterRef defined on the given indirectAddressRef element.

— Returns: registerRef of type String - The referenced register
— Input: indirectAddressRefID of type String - Handle to an indirectAddressRef element

#### F.7.53.19 getIndirectAddressRefRegisterRefID

Description: Returns the handle to the registerRef defined on the given indirectAddressRef element.

— Returns: registerRefID of type String - Handle to the registerRef element
— Input: indirectAddressRefID of type String - Handle to an indirectAddressRef element

#### F.7.53.20 getIndirectDataRefAddressBlockRefByName

Description: Returns the addressBlockRef defined on the given indirectDataRef element.

— Returns: addressBlockRef of type String - The referenced addressBlock
— Input: indirectDataRefID of type String - Handle to an indirectDataRef element

#### F.7.53.21 getIndirectDataRefAddressBlockRefID

Description: Returns the handle to the addressBlockRef defined on the given indirectDataRef element.

— Returns: addressBlockRefID of type String - Handle to the addressBlockRef element
— Input: indirectDataRefID of type String - Handle to an indirectDataRef element

#### F.7.53.22 getIndirectDataRefAddressSpaceRefByName

Description: Returns the addressBlockRef defined on the given indirectDataRef element.

— Returns: addressSpaceRef of type String - The referenced addressSpace
— Input: indirectDataRefID of type String - Handle to an indirectDataRef element

#### F.7.53.23 getIndirectDataRefAddressSpaceRefID

Description: Returns the handle to the addressSpaceRef defined on the given indirectDataRef element.

— Returns: addressSpaceRefID of type String - Handle to the addressSpaceRef element
— Input: indirectDataRefID of type String - Handle to an indirectDataRef element

#### F.7.53.24 getIndirectDataRefAlternateRegisterRefByName

Description: Returns the addressBlockRef defined on the given indirectDataRef element.

— Returns: alternateRegisterRef of type String - The referenced alternateRegister
— Input: indirectDataRefID of type String - Handle to an indirectDataRef element

#### F.7.53.25 getIndirectDataRefAlternateRegisterRefID

Description: Returns the handle to the alternateRegisterRef defined on the given indirectDataRef element.

— Returns: alternateRegisterRefID of type String - Handle to the alternateRegisterRef ele-

ment

— Input: indirectDataRefID of type String - Handle to an indirectDataRef element

#### F.7.53.26 getIndirectDataRefBankRefByNames

Description: Returns the bankRef defined on the given indirectDataRef element.

— Returns: bankRef of type String - The referenced bank
— Input: indirectDataRefID of type String - Handle to an indirectDataRef element

#### F.7.53.27 getIndirectDataRefBankRefIDs

Description: Returns the handles to all the bankRefs defined on the given indirectDataRef element.

— Returns: bankRefIDs of type String - List of handles to the bankRef elements
— Input: indirectDataRefID of type String - Handle to an indirectDataRef element

#### F.7.53.28 getIndirectDataRefFieldRefByName

Description: Returns the fieldRef defined on the given indirectDataRef element.

— Returns: fieldRef of type String - The referenced field
— Input: indirectDataRefID of type String - Handle to an indirectDataRef element

#### F.7.53.29 getIndirectDataRefFieldRefID

Description: Returns the handle to the fieldRef defined on the given indirectDataRef element.

— Returns: fieldRefID of type String - Handle to the fieldRef element
— Input: indirectDataRefID of type String - Handle to an indirectDataRef element

#### F.7.53.30 getIndirectDataRefMemoryMapRefByName

Description: Returns the memoryMapRef defined on the given indirectDataRef element.

— Returns: memoryMapRef of type String - The referenced memoryMap
— Input: indirectDataRefID of type String - Handle to an indirectDataRef element

#### F.7.53.31 getIndirectDataRefMemoryMapRefID

Description: Returns the handle to the memoryMapRef defined on the given indirectDataRef element.

— Returns: memoryMapRefID of type String - Handle to the memoryMapRef element
— Input: indirectDataRefID of type String - Handle to an indirectDataRef element

#### F.7.53.32 getIndirectDataRefMemoryRemapRefByID

Description: Returns the handle to a memoryRemap element from the given indirectDataRef element.

— Returns: memoryRemapID of type String - Handle to a memoryRemap element
— Input: indirectDataRefID of type String - Handle to a indirectDataRef element

#### F.7.53.33 getIndirectDataRefMemoryRemapRefByName

Description: Returns the memoryRemapRef value from the given indirectDataRef element.

— Returns: memoryRemapRef of type String - The memoryRemapRef value
— Input: indirectDataRefID of type String - Handle to a indirectDataRef element

#### F.7.53.34 getIndirectDataRefMemoryRemapRefID

Description: Returns the handle to a memoryRemapRef element from the given indirectDataRef element.

— Returns: memoryRemapRefID of type String - Handle to a memoryRemapRef element
— Input: indirectDataRefID of type String - Handle to a indirectDataRef element

#### F.7.53.35 getIndirectDataRefRegisterFileRefByNames

Description: Returns the registerFileRef defined on the given indirectDataRef element.

— Returns: registerFileRef of type String - List of registerFileRefs
— Input: indirectDataRefID of type String - Handle to an indirectDataRef element

#### F.7.53.36 getIndirectDataRefRegisterFileRefIDs

Description: Returns the handles to all the registerFileRefs defined on the given indirectDataRef element.

— Returns: registerFileRefIDs of type String - List of handles to the registerFileRef elements
— Input: indirectDataRefID of type String - Handle to an indirectDataRef element

#### F.7.53.37 getIndirectDataRefRegisterRefByName

Description: Returns the registerRef defined on the given indirectDataRef element.

— Returns: registerRef of type String - The referenced register
— Input: indirectDataRefID of type String - Handle to an indirectDataRef element

#### F.7.53.38 getIndirectDataRefRegisterRefID

Description: Returns the handle to the registerRef defined on the given indirectDataRef element.

— Returns: registerRefID of type String - Handle to the registerRef element
— Input: indirectDataRefID of type String - Handle to an indirectDataRef element

#### F.7.53.39 getIndirectInterfaceBitsInLau

Description: Returns the bitsInLau resolved value on an indirectInterface element

— Returns: value of type Long - The bitsInLau resolved value
— Input: indirectInterfaceID of type String - Handle to an indirectInterface element

#### F.7.53.40 getIndirectInterfaceBitsInLauExpression

Description: Returns the bitsInLau expression defined on the given indirectInterface element

— Returns: bitsInLauExpression of type String - The bitsInLau expression
— Input: indirectInterfaceID of type String - Handle to an indirectInterface element

#### F.7.53.41 getIndirectInterfaceEndianness

Description: Returns the endianness defined on the given indirectInterface element.

— Returns: value of type String - The endianness value
— Input: indirectInterfaceID of type String - Handle to an indirectInterface element

#### F.7.53.42 getIndirectInterfaceIndirectAddressRefID

Description: Returns the handle to indirectAddressRef defined on the given indirectInterface element.

— Returns: indirectAddressRefID of type String - Handle to the indirectAddressRef element
— Input: indirectInterfaceID of type String - Handle to an indirectInterface element

#### F.7.53.43 getIndirectInterfaceIndirectDataRefID

Description: Returns the handle to the indirectDataRef defined on the given indirectInterface element.

— Returns: indirectDataRefID of type String - Handle to the indirectDataRef element
— Input: indirectInterfaceID of type String - Handle to an indirectInterface element

#### F.7.53.44 getIndirectInterfaceMemoryMapRefByID

Description: Returns the handle to the memoryMap referenced from the given indirectInterface element.

— Returns: memoryMapID of type String - Handle to the referenced memoryMap element
— Input: indirectInterfaceID of type String - Handle to an indirectInterface element

#### F.7.53.45 getIndirectInterfaceMemoryMapRefByName

Description: Returns the memoryMapRef defined on the given indirectInterface element.

— Returns: memoryMapRef of type String - The referenced memoryMap
— Input: indirectInterfaceID of type String - Handle to an indirectInterface element

#### F.7.53.46 getIndirectInterfaceTransparentBridgeIDs

Description: Returns the the list of handles to transparent bridges defined on the given indirectInterface
element.

— Returns: transparentBridgeIDs of type String - List of handles to the transparentBridge elements

— Input: indirectInterfaceID of type String - Handle to an indirectInterface element

### F.7.54 Indirect interface (EXTENDED)

#### F.7.54.1 addIndirectAddressRefBankRef

Description: Adds a bankRef element on an indirectAddressRef element.

— Returns: bankRefID of type String - the identifier on a bankRef element
— Input: indirectAddressRefID of type String - Handle to an indirectAddressRef on an

indirectInterface element

— Input: bankRef of type String - the bankRef to add

#### F.7.54.2 addIndirectAddressRefRegisterFileRef

Description: Adds a registerFileRef on an indirectAddressRef element.

— Returns: registerFileRefID of type String - the added registerFileRef identifier
— Input: indirectAddressRefID of type String - Handle to an indirectAddressRef on an

indirectInterface element

— Input: registerFileRef of type String - the registerFile reference to set on an

indirectAddressRef

#### F.7.54.3 addIndirectDataRefBankRef

Description: Adds a bankRef element on an indirectDataRef element.

— Returns: bankRefID of type String - the identifier on a bankRef element

— Input: indirectDataRefID of type String - Handle to an indirectAddressRef on an

indirectDataRef element

— Input: bankRef of type String - The bankRef to add

#### F.7.54.4 addIndirectDataRefRegisterFileRef

Description: Adds a registerFileRef on an indirectDataRef element.

— Returns: registerFileRefID of type String - The added registerFileRef identifier
— Input: indirectDataRefID of type String - Handle to an indirectDataRef on an

indirectInterface element

— Input: registerFileRef of type String - The registerFile reference to set on an indirectDataRef

#### F.7.54.5 addIndirectInterfaceTransparentBridge

Description: Adds bridge with the given busInterfaceRef to the given indirectInterface element.

— Returns: transparentBridgeID of type String - Handle of a transparentBridge element
— Input: indirectInterfaceID of type String - Handle to an indirectInterface element
— Input: initiatorRef of type String - Value for initiatorRef attribute

#### F.7.54.6 removeAliasOfMemoryRemapRef

Description: Removes the memoryRemap reference on an aliasOf element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: aliasOfID of type String - Handle to an aliasOf element

#### F.7.54.7 removeBroadcastToAddressSpaceRef

Description: Removes the addressSpaceRef on an broadcastTo element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: broadcastToID of type String - Handle to a broadcastTo element

#### F.7.54.8 removeIndirectAddressRefAddressBlockRef

Description: Removes addressBlockRef on an indirectAddressRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectAddressRefID of type String - Handle to an indirectAddressRef on an

indirectInterface element

#### F.7.54.9 removeIndirectAddressRefAddressSpaceRef

Description: Removes the addressSpaceRef on an indirectAddressRef element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectAddressRefID of type String - Handle to an indirectAddressRef element

#### F.7.54.10 removeIndirectAddressRefAlternateRegisterRef

Description: Removes an alternateRegisterRef on an indirectAddressRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectAddressRefID of type String - Handle of an indirectAddresRef element

#### F.7.54.11 removeIndirectAddressRefBankRef

Description: Removes a bank reference from an indirectAddressRef element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: bankRefID of type String - Handle to a bankRef element

#### F.7.54.12 removeIndirectAddressRefMemoryMapRef

Description: Removes the memoryMap reference on an indirectAddressRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectAddressRefID of type String - Handle to an indirectAddressRef on an

indirectInterface element

#### F.7.54.13 removeIndirectAddressRefMemoryRemapRef

Description: Removes the memoryRemap reference on an indirectDataRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectAddressRefID of type String - Handle to an indirectAddressRef on an

indirectInterface element

#### F.7.54.14 removeIndirectAddressRefRegisterFileRef

Description: Removes the given registerFileRef from its containing indirectAddressRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerFileRefID of type String - Handle to a registerFileRef on an

indirectAddressRef element

#### F.7.54.15 removeIndirectAddressRefRegisterRef

Description: Removes the registerRef on an indirectAddressRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectAddressRefID of type String - Handle to an indirectAddressRef on an

indirectInterface element

#### F.7.54.16 removeIndirectDataRefAddressBlockRef

Description: Removes addressBlockRef on an indirectDataRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectDataRefID of type String - Handle to an indirectDataRef on an

indirectInterface element

#### F.7.54.17 removeIndirectDataRefAddressSpaceRef

Description: Removes the addressSpace reference on an indirectDataRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectDataRefID of type String - Handle to an indirectDataRef on an

indirectInterface element

#### F.7.54.18 removeIndirectDataRefAlternateRegisterRef

Description: Removes an alternateRegisterRef on an indirectDataRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectDataRefID of type String - Handle of an indirectDataRef element

#### F.7.54.19 removeIndirectDataRefBankRef

Description: Removes a bank reference from an indirectDataRef element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: bankRefID of type String - Handle to a bankRef element

#### F.7.54.20 removeIndirectDataRefMemoryMapRef

Description: Removes the memoryMap reference on an indirectDataRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectDataRefID of type String - Handle to an indirectDataRef on an

indirectInterface element

#### F.7.54.21 removeIndirectDataRefMemoryRemapRef

Description: Removes the memoryRemap reference on an indirectDataRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectDataRefID of type String - Handle to an indirectDataRef on an

indirectInterface element

#### F.7.54.22 removeIndirectDataRefRegisterFileRef

Description: Removes the given registerFileRef from its containing indirectDataRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerFileRefID of type String - Handle to a registerFileRef on an

indirectDataRef element

#### F.7.54.23 removeIndirectDataRefRegisterRef

Description: Removes the registerRef on an indirectDataRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectDataRefID of type String - Handle to an indirectDataRef on an

indirectInterface element

#### F.7.54.24 removeIndirectInterfaceEndianness

Description: Removes the endianness from the given indirectInterface element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectInterfaceID of type String - Handle to an indirectInterface element

#### F.7.54.25 removeIndirectInterfaceTransparentBridge

Description: Removes the given bridge element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)

— Input: transparentBridgeID of type String - Handle to a transparentBridge element

#### F.7.54.26 setIndirectAddressRefAddressBlockRef

Description: Sets addressBlockRef on an indirectAddressRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectAddressRefID of type String - Handle to an indirectAddressRef on an

indirectInterface element

— Input: addressBlockRef of type String - The addressBlock reference to set

#### F.7.54.27 setIndirectAddressRefAddressSpaceRef

Description: Sets the addressSpace reference on an indirectAddressRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectAddressRefID of type String - Handle to an indirectAddressRef element
— Input: addressSpaceRef of type String - Name of the referenced addressSpace on an

indirectAddressRef element

#### F.7.54.28 setIndirectAddressRefAlternateRegisterRef

Description: Sets an alternateRegisterRef on an indirectAddressRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectAddressRefID of type String - Handle of an indirectAddresRef element
— Input: alternateRegisterRef of type String - The alternateRegisterRef value to set

#### F.7.54.29 setIndirectAddressRefFieldRef

Description: Sets the fieldRef reference on an indirectAddressRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectAddressRefID of type String - Handle to an indirectAddressRef element
— Input: fieldRef of type String - Name of the referenced field on an indirectAddressRef element

#### F.7.54.30 setIndirectAddressRefMemoryMapRef

Description: Sets the memoryMap reference on an indirectAddressRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectAddressRefID of type String - Handle to an indirectAddressRef element
— Input: memoryMapRef of type String - Name of the referenced memoryMap on an

indirectAddressRef element

#### F.7.54.31 setIndirectAddressRefMemoryRemapRef

Description: Sets memoryRemapRef on an indirectAddressRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectAddressRefID of type String - Handle to an indirectAddressRef on an

indirectInterface element

— Input: memoryRemapRef of type String - the memoryRemap reference to set

#### F.7.54.32 setIndirectAddressRefRegisterRef

Description: Sets the registerRef on an indirectAddressRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectAddressRefID of type String - Handle to an indirectAddressRef on an

indirectInterface element

— Input: registerRef of type String - Name of the referenced register element

#### F.7.54.33 setIndirectDataRefAddressBlockRef

Description: Sets addressBlockRef on an indirectDataRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectDataRefID of type String - Handle to an indirectDataRef on an

indirectInterface element

— Input: addressBlockRef of type String - the addressBlock reference to set

#### F.7.54.34 setIndirectDataRefAddressSpaceRef

Description: Sets the addressSpace reference on an indirectDataRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectDataRefID of type String - Handle to an indirectDataRef on an

indirectInterface element

— Input: addressSpaceRef of type String - Name of the referenced addressSpace on an

indirectDataRef element

#### F.7.54.35 setIndirectDataRefAlternateRegisterRef

Description: Sets an alternateRegisterRef on an indirectDataRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectDataRefID of type String - Handle of an indirectDataRef element
— Input: alternateRegisterRef of type String - the alternateRegisterRef value to set

#### F.7.54.36 setIndirectDataRefFieldRef

Description: Sets the fieldRef reference on an indirectDataRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectDataRefID of type String - Handle to an indirectDataRef element
— Input: fieldRef of type String - Name of the referenced field on an indirectDataRef element

#### F.7.54.37 setIndirectDataRefMemoryMapRef

Description: Sets the memoryMap reference on an indirectDataRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectDataRefID of type String - Handle to an indirectDataRef on an

indirectInterface element

— Input: memoryMapRef of type String - Name of the referenced memoryMap on an

indirectDataRef element

#### F.7.54.38 setIndirectDataRefMemoryRemapRef

Description: Sets memoryRemapRef on an indirectDataRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectDataRefID of type String - Handle to an indirectDataRef on an

indirectInterface element

— Input: memoryRemapRef of type String - The memoryRemap reference to set

#### F.7.54.39 setIndirectDataRefRegisterRef

Description: Sets the registerRef on an indirectDataRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectDataRefID of type String - Handle to an indirectDataRef on an

indirectInterface element

— Input: registerRef of type String - Name of the referenced register

#### F.7.54.40 setIndirectInterfaceEndianness

Description: Sets the endianness with the given value for the given indirectInterface element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectInterfaceID of type String - Handle to an indirectInterface element
— Input: value of type String - Endianness value

#### F.7.54.41 setIndirectInterfaceMemoryMapRef

Description: Sets the memoryMapRef on an indirectInterface element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indirectInterfaceID of type String - Handle to an indirectInterface element
— Input: memoryMapRef of type String - The memoryMap reference to be set

### F.7.55 Instantiation (BASE)

#### F.7.55.1 getAbstractionTypeAbstractionRefID

Description: Returns the handle to the abstractionRef defined on the given abstractionType element.

— Returns: abstractionRefID of type String - Handle to the abstractionRef element
— Input: abstractionTypeID of type String - Handle to an abstractionType element

#### F.7.55.2 getAbstractorInstanceAbstractorRefID

Description: Returns the handle to the abstractorRef defined on the given abstractorInstance element.

— Returns: abstractorRefID of type String - Handle to the abstractorRef element
— Input: abstractorInstanceID of type String - Handle to an abstractorInstance element

#### F.7.55.3 getComponentInstanceComponentRefID

Description: Returns the handle to the componentRef defined on the given componentInstance element.

— Returns: componentRefID of type String - Handle to the componentRef element
— Input: componentInstanceID of type String - Handle to a componentInstance element

#### F.7.55.4 getComponentInstantiationArchitectureName

Description: Returns the architectureName defined on the given componentInstantiation element.

— Returns: architectureName of type String - The architecture name
— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

#### F.7.55.5 getComponentInstantiationClearboxElementRefIDs

Description: Returns
componentInstantiation element.

the handles

to all

the clearboxElementRefs defined on

the given

— Returns: clearboxElementRefIDs of type String - List of handles to the

clearboxElementRef elements

— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

#### F.7.55.6 getComponentInstantiationConfigurationName

Description: Returns the configurationName defined on the given componentInstantiation element.

— Returns: configurationName of type String - The configuration name
— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

#### F.7.55.7 getComponentInstantiationConstraintSetRefIDs

Description: Returns the handles to all the constraintSetRefs defined on the given componentInstantiation
element.

— Returns: constraintSetRefIDs of type String - List of handles to constraintSetRef elements
— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

#### F.7.55.8 getComponentInstantiationDefaultFileBuilderIDs

Description: Returns the handles to all the defaultFileBuilders defined on the given componentInstantiation
element.

— Returns: fileBuilderIDs of type String - List of handles to fileBuilder elements
— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

#### F.7.55.9 getComponentInstantiationFileSetRefIDs

Description: Returns the handles to all the fileSetRefs defined on the given componentInstantiation element.

— Returns: fileSetRefIDs of type String - List of handles to fileSetRef elements
— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

#### F.7.55.10 getComponentInstantiationIsVirtual

Description: Returns the isVirtual element defined on the given componentInstantiation element.

— Returns: value of type Boolean - The isVirtual value

— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

#### F.7.55.11 getComponentInstantiationLanguage

Description: Returns the language defined on the given componentInstantiation element.

— Returns: language of type String - The language defined
— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

#### F.7.55.12 getComponentInstantiationLanguageID

Description: Returns the handle to the language defined on the given componentInstantiation element.

— Returns: language of type String - Handle to the language element
— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

#### F.7.55.13 getComponentInstantiationLibraryName

Description: Returns the libraryName defined on the given componentInstantiation element.

— Returns: libraryName of type String - The library name
— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

#### F.7.55.14 getComponentInstantiationModuleName

Description: Returns the moduleName defined on the given componentInstantiation element.

— Returns: moduleName of type String - The module name
— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

#### F.7.55.15 getComponentInstantiationPackageName

Description: Returns the packageName defined on the given componentInstantiation element.

— Returns: packageName of type String - The package name
— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

#### F.7.55.16 getDesignConfigurationInstantiationDesignConfigurationRefByID

Description: Returns the handle to the designConfiguration instance referenced from the given
designConfigurationInstantiation element.

— Returns: designConfigurationID of type String - Handle to the referenced

designConfiguration object

— Input: designConfigurationInstantiationID of type String - Handle to a

designConfigurationInstantiation element

#### F.7.55.17 getDesignConfigurationInstantiationDesignConfigurationRefByVLNV

Description: Returns
designConfigurationInstantiation element.

the VLNV of

the designConfiguration

referenced

from

the given

— Returns: VLNV of type String - The VLNV of the referenced designConfiguration object
— Input: designConfigurationInstantiationID of type String - Handle to a

designConfigurationInstantiation element

#### F.7.55.18 getDesignConfigurationInstantiationDesignConfigurationRefID

Description: Returns
designConfigurationInstantiation element.

the handle

to

the designConfigurationRef defined on

the given

— Returns: designConfigurationRefID of type String - Handle to the designConfigurationRef element

— Input: designConfigurationInstantiationID of type String - Handle to a

designConfigurationInstantiation element

#### F.7.55.19 getDesignConfigurationInstantiationLanguage

Description: Returns the language defined on the given designConfigurationInstantiation element.

— Returns: language of type String - The language defined
— Input: designConfigurationInstantiationID of type String - Handle to a

designConfigurationInstantiation element

#### F.7.55.20 getDesignConfigurationInstantiationLanguageID

Description: Returns the handle to the language defined on the given designConfigurationInstantiation
element.

— Returns: language of type String - Handle to the language element
— Input: designConfigurationInstantiationID of type String - Handle to a

designConfigurationInstantiation element

#### F.7.55.21 getDesignInstantiationDesignRefByID

Description: Returns the handle to the design instance referenced from the given designInstantiation
element.

— Returns: designID of type String - Handle to the referenced design object
— Input: designInstantiationID of type String - Handle to a designInstantiation element

#### F.7.55.22 getDesignInstantiationDesignRefByVLNV

Description: Returns the VLNV of the design referenced from the given designInstantiation element.

— Returns: VLNV of type String - The VLNV of the referenced design object
— Input: designInstantiationID of type String - Handle to a designInstantiation element

#### F.7.55.23 getDesignInstantiationDesignRefID

Description: Returns the handle to the designRef defined on the given designInstantiation element.

— Returns: designRefID of type String - Handle to the designRef element
— Input: designInstantiationID of type String - Handle to a designInstantiation element

#### F.7.55.24 getExternalTypeDefinitionsTypeDefinitionsRefID

Description: Returns the handle to the typeDefinitionsRef defined on the given externalTypeDefinitions
element.

— Returns: typeDefinitionsRefID of type String - Handle to the typeDefinitionsRef element
— Input: externalTypeDefinitionsID of type String - Handle to an externalTypeDefinitions element

#### F.7.55.25 getFileSetRefLocalName

Description: Returns the locaName defined on the given fileSetRef element.

— Returns: localName of type String - The local name
— Input: fileSetRefID of type String - Handle to a fileSetRef element

#### F.7.55.26 getGeneratorChainSelectorGeneratorChainRefID

Description: Returns the handle to the generatorChainRef defined on the given generatorChainSelector
element.

— Returns: generatorChainRefID of type String - Handle to the generatorChainRef element
— Input: generatorChainSelectorID of type String - Handle to a generatorChainSelector element

### F.7.56 Instantiation (EXTENDED)

#### F.7.56.1 addComponentInstantiationClearboxElementRef

Description: Adds clearboxElementRef with the given name, pathSegmentName, and indices to the given.
componentInstantiation element

— Returns: clearboxElementRefID of type String - Handle to a new clearboxElementRef
— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

— Input: name of type String - The clearboxElementRef name
— Input: pathSegmentValue of type String - The clearboxElementRef pathSegment value

#### F.7.56.2 addComponentInstantiationConstraintSetRef

Description: Adds constraintRefSet with the given localName to the given componentInstantiation element.

— Returns: constraintSetRefID of type String - Handle to a new constraintSetRef
— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

— Input: localName of type String - ConstraintSetRef localName

#### F.7.56.3 addComponentInstantiationDefaultFileBuilder

Description: Adds defaultFileBuilder with the given fileType to the given componentInstantiation element.

— Returns: fileBuilderID of type String - Handle to a new fileBuilder
— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

— Input: fileType of type String - The defaultFileBuilder fileType

#### F.7.56.4 addComponentInstantiationFileSetRef

Description: Adds fileSetRef with the given localName to the given componentInstantiation element.

— Returns: fileSetRefID of type String - Handle to a new fileSetRef
— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

— Input: localName of type String - The fileSetRef localName

#### F.7.56.5 removeComponentInstantiationArchitectureName

Description: Removes architectureName from the given componentInstantiation element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

#### F.7.56.6 removeComponentInstantiationClearboxElementRef

Description: Removes the given clearboxElementRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: clearboxElementRefID of type String - Handle to a clearboxElementRef element

#### F.7.56.7 removeComponentInstantiationConfigurationName

Description: Removes configurationName from the given componentInstantiation element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

#### F.7.56.8 removeComponentInstantiationConstraintSetRef

Description: Removes the given constraintSetRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: constraintSetRefID of type String - Handle to a constraintSetRef element

#### F.7.56.9 removeComponentInstantiationDefaultFileBuilder

Description: Removes the given defaultFileBuilder element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileBuilderID of type String - Handle to a fileBuilder element

#### F.7.56.10 removeComponentInstantiationFileSetRef

Description: Removes the given fileSetRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fileSetRefID of type String - Handle to a fileSetRef element

#### F.7.56.11 removeComponentInstantiationIsVirtual

Description: Removes isVirtual from the given componentInstantiation element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)

— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

#### F.7.56.12 removeComponentInstantiationLanguage

Description: Removes language from the given componentInstantiation element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

#### F.7.56.13 removeComponentInstantiationLibraryName

Description: Removes libraryName from the given componentInstantiation element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

#### F.7.56.14 removeComponentInstantiationModuleName

Description: Removes moduleName from the given componentInstantiation element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

#### F.7.56.15 removeComponentInstantiationPackageName

Description: Removes packageName from the given componentInstantiation element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

#### F.7.56.16 removeDesignConfigurationInstantiationLanguage

Description: Removes language from the given designConfigurationInstantiation element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: designConfigurationInstantiationID of type String - Handle to a

designConfigurationInstantiation element

#### F.7.56.17 setComponentInstantiationArchitectureName

Description: Sets architectureName with the given value for the given componentInstantiation element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

— Input: architectureName of type String - ArchitectureName value

#### F.7.56.18 setComponentInstantiationConfigurationName

Description: Sets configurationName with the given value for the given componentInstantiation element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)

— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

— Input: configurationName of type String - ConfigurationName value

#### F.7.56.19 setComponentInstantiationIsVirtual

Description: Sets isVirtual with the given value for the given componentInstantiation element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

— Input: value of type Boolean - isVirtual value

#### F.7.56.20 setComponentInstantiationLanguage

Description: Sets language with the given value for the given componentInstantiation element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

— Input: language of type String - Language value

#### F.7.56.21 setComponentInstantiationLibraryName

Description: Sets libraryName with the given value for the given componentInstantiation element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

— Input: libraryName of type String - LibraryName value

#### F.7.56.22 setComponentInstantiationModuleName

Description: Sets moduleName with the given value for the given componentInstantiation element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

— Input: moduleName of type String - ModuleName value

#### F.7.56.23 setComponentInstantiationPackageName

Description: Sets packageName with the given value for the given componentInstantiation element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: componentInstantiationID of type String - Handle to a componentInstantiation element

— Input: packageName of type String - PackageName value

#### F.7.56.24 setDesignConfigurationInstantiationDesignConfigurationRef

Description:
designConfigurationInstantiation element.

Sets

the

designConfigurationRef with

the

given

value

for

the

given

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)

— Input: designConfigurationInstantiationID of type String - Handle to an

designConfigurationInstantiation element

— Input: designConfigurationVLNV of type String[] - The designConfiguration reference

#### F.7.56.25 setDesignConfigurationInstantiationLanguage

Description: Sets language with the given value for the given designConfigurationInstantiation element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: designConfigurationInstantiationID of type String - Handle to a

designConfigurationInstantiation element

— Input: language of type String - The designConfigurationInstantiation language

#### F.7.56.26 setDesignInstantiationDesignRef

Description: Sets the designRef with the given value for the given designInstantiation element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: designInstantiationID of type String - Handle to an designInstantiation element
— Input: designVLNV of type String[] - The design reference

### F.7.57 Memory map (BASE)

#### F.7.57.1 getAddressBlockAccessPolicyIDs

Description: Returns the handles to all the accessPolicies defined on the given addressBlock element.

— Returns: accessPoliciesIDs of type String - List of handles to the accessPolicies elements
— Input: addressBlockID of type String - Handle to an addressBlock element

#### F.7.57.2 getAddressBlockAddressBlockDefinitionRefByExternalTypeDefID

Description: Returns the handle to the externalTypeDefinitions referenced by the typeDefinitions attribute
of the addressBlockDefinitionRef defined on the given addressBlock element.

— Returns: externalTypeDefinitionsID of type String - Handle to the
externalTypeDefinitions element referenced by the typeDefinitions attribute
— Input: addressBlockID of type String - Handle to an addressBlock element

#### F.7.57.3 getAddressBlockAddressBlockDefinitionRefByID

Description: Returns the handle to the addressBlockDefinition (defined in the typeDefinitions root object)
referenced from the given addressBlock element.

— Returns: addressBlockDefinitionID of type String - Handle to the referenced

addressBlockDefinition

— Input: addressBlockID of type String - Handle to an addressBlock element

#### F.7.57.4 getAddressBlockAddressBlockDefinitionRefByName

Description: Returns the addressBlockDefinition referenced from the given addressBlock element.

— Returns: addressBlockDefinitionRef of type String - The referenced

addressBlockDefinition

— Input: addressBlockID of type String - Handle to an addressBlock element

#### F.7.57.5 getAddressBlockAddressBlockDefinitionRefID

Description: Returns the handle to the addressBlockDefinitionRef element defined in the given
addressBlock element.

— Returns: addressBlockDefinitionRefID of type String - Handle to the

addressBlockDefinitionRef element

— Input: addressBlockID of type String - Handle to an addressBlock element

#### F.7.57.6 getAddressBlockArrayID

Description: Returns the handle to the array defined on the given addressBlock element.

— Returns: arrayID of type String - Handle to the addressBlock array
— Input: addressBlockID of type String - Handle to an addressBlock element

#### F.7.57.7 getAddressBlockBaseAddress

Description: Returns the baseAddress defined on the given addressBlock element.

— Returns: baseAddress of type Long - The base address
— Input: addressBlockID of type String - Handle to an addressBlock element

#### F.7.57.8 getAddressBlockBaseAddressExpression

Description: Returns the baseAddress expression defined on the given addressBlock element.

— Returns: baseAddressExpression of type String - The baseAddress expression
— Input: addressBlockID of type String - Handle to an addressBlock element

#### F.7.57.9 getAddressBlockBaseAddressID

Description: Returns the handle to the baseAddress defined on the given addressBlock element.

— Returns: baseAddressID of type String - Handle to the baseAddress element
— Input: addressBlockID of type String - Handle to an addressBlock element

#### F.7.57.10 getAddressBlockRange

Description: Returns the range value defined on the given address Block element.

— Returns: range of type Long - The addressBlock range value
— Input: addressBlockID of type String - Handle to an addressBlock element

#### F.7.57.11 getAddressBlockRangeExpression

Description: Returns the range expression defined on the given addressBlock element.

— Returns: rangeExpression of type String - The range expression
— Input: addressBlockID of type String - Handle to an addressBlock element

#### F.7.57.12 getAddressBlockRangeID

Description: Returns the handle to the range defined on the given addressBlock element.

— Returns: rangeID of type String - Handle to the range element
— Input: addressBlockID of type String - Handle to an addressBlock element

#### F.7.57.13 getAddressBlockRefIndexIDs

Description: Returns the handles to all the indices defined on the given addressBlockRef element.

— Returns: indexID of type String - List of handles to the index elements
— Input: addressBlockRefID of type String - Handle to an addressBlockRef element

#### F.7.57.14 getAddressBlockRegisterFileIDs

Description: Returns the handles to all the registerFiles defined on the given addressBlock element.

— Returns: registerFileIDs of type String - List of handles to registerFile elements
— Input: addressBlockID of type String - Handle to an addressBlock element

#### F.7.57.15 getAddressBlockRegisterIDs

Description: Returns the handles to all the registers defined on the given addressBlock element.

— Returns: registerIDs of type String - List of handles to register elements
— Input: addressBlockID of type String - Handle to an addressBlock element

#### F.7.57.16 getAddressBlockTypeIdentifier

Description: Returns the typeIdentifier defined on the given addressBlock element.

— Returns: typeIdentifier of type String - The typeIdentifier value
— Input: addressBlockID of type String - Handle to an addressBlock element

#### F.7.57.17 getAddressBlockUsage

Description: Returns the usage defined on the given addressBlock element.

— Returns: usage of type String - The addressBlock usage
— Input: addressBlockID of type String - Handle to an addressBlock element

#### F.7.57.18 getAddressBlockVolatility

Description: Returns the volatile value defined on the given addressBlock element.

— Returns: volatile of type Boolean - The volatile value
— Input: addressBlockID of type String - Handle to an addressBlock element

#### F.7.57.19 getAddressBlockWidth

Description: Returns the width value defined on the given addressBlock element.

— Returns: width of type Long - The addressBlock width value
— Input: addressBlockID of type String - Handle to an addressBlock element

#### F.7.57.20 getAddressBlockWidthExpression

Description: Returns the width expression defined on the given addressBlock element.

— Returns: widthExpression of type String - The width expression
— Input: addressBlockID of type String - Handle to an addressBlock element

#### F.7.57.21 getAddressBlockWidthID

Description: Returns the handle to the width defined on the given addressBlock element.

— Returns: widthID of type String - Handle to the width element
— Input: addressBlockID of type String - Handle to an addressBlock element

#### F.7.57.22 getAliasOfAddressBlockRefByName

Description: Returns the addressBlockRef defined on the given aliasOf element.

— Returns: addressBlockRef of type String - The refrenced addressBlock
— Input: aliasOfID of type String - Handle to an aliasOf element

#### F.7.57.23 getAliasOfAddressBlockRefID

Description: Returns the handle to the addressBlockRef defined on the given aliasOf element.

— Returns: addressBlockRefID of type String - Handle to the addressBlockRef element
— Input: aliasOfID of type String - Handle to an aliasOf element

#### F.7.57.24 getAliasOfBankRefByNames

Description: Returns all the bankRefs defined on the given aliasOf element.

— Returns: bankRef of type String - List of bankRef names
— Input: aliasOfID of type String - Handle to an aliasOf element

#### F.7.57.25 getAliasOfBankRefIDs

Description: Returns the handles to the bankRefs defined on the given aliasOf element.

— Returns: bankRefID of type String - List of handles to the bankRef elements
— Input: aliasOfID of type String - Handle to an aliasOf element

#### F.7.57.26 getAliasOfMemoryMapRefByName

Description: Returns the memoryMapRef defined on the given aliasOf element.

— Returns: memoryMapRef of type String - The referenced memoryMap
— Input: aliasOfID of type String - Handle to an aliasOf element

#### F.7.57.27 getAliasOfMemoryMapRefID

Description: Returns the handle to the memoryMapRef defined on the given AliasOf element.

— Returns: memoryMapRefID of type String - Handle to the memoryMapRef element
— Input: aliasOfID of type String - Handle to an aliasOf element

#### F.7.57.28 getAliasOfMemoryRemapRefByID

Description: Returns a handle to a memoryRemap defined on the given aliasOf element.

— Returns: memoryMapID of type String - Handle to a memoryRemap
— Input: aliasOfID of type String - Handle to an aliasOf element

#### F.7.57.29 getAliasOfMemoryRemapRefByName

Description: Returns the memoryRemapRef defined on the given aliasOf element.

— Returns: memoryRemapRef of type String - The memoryRemap reference
— Input: aliasOfID of type String - Handle to an aliasOf element

#### F.7.57.30 getAliasOfMemoryRemapRefID

Description: Returns a handle to a memoryRemapRef defined on the given aliasOf element.

— Returns: memoryRemapRefID of type String - Handle to a memoryRemapRef
— Input: aliasOfID of type String - Handle to an aliasOf element

#### F.7.57.31 getBankAddressBlockIDs

Description: Returns the handles to all the addressBlocks defined on the given bank element.

— Returns: addressBlockIDs of type String - List of handles to the addressBlock elements
— Input: bankID of type String - Handle to a bank element

#### F.7.57.32 getBankBankDefinitionRefByExternalTypeDefID

Description: Returns the handle to the externalTypeDefinitions referenced by the typeDefinitions attribute
of the bankDefinitionRef defined on the given bank element.

— Returns: bankDefinitionID of type String - Handle to the externalTypeDefinitions element

referenced by the typeDefinitions attribute

— Input: bankID of type String - Handle to a bank element

#### F.7.57.33 getBankBankDefinitionRefByID

Description: Returns the handle to the bankDefinition referenced from the given bank element.

— Returns: bankDefinitionID of type String - Handle to the referenced bankDefinition element
— Input: bankID of type String - Handle to a bank element

#### F.7.57.34 getBankBankDefinitionRefByName

Description: Returns the bankDefinitionRef defined on the given bank element.

— Returns: bankDefinitionRef of type String - The referenced bankDefinition
— Input: bankID of type String - Handle to a bank element

#### F.7.57.35 getBankBankDefinitionRefID

Description: Returns the handle to the bankDefinitionRef defined on the given bank element.

— Returns: bankDefinitionRefID of type String - Handle to the bankDefinitionRef element
— Input: bankID of type String - Handle to a bank element

#### F.7.57.36 getBankBankIDs

Description: Returns the handles to all the banks defined on the given bank element.

— Returns: bankIDs of type String - List of handles to the bank elements
— Input: bankID of type String - Handle to a bank element

#### F.7.57.37 getBankBaseAddress

Description: Returns the baseAddress defined on the given bank or localBank element.

— Returns: baseAddress of type Long - The base address
— Input: bankOrLocalBankID of type String - Handle to a bank or localBank element

#### F.7.57.38 getBankBaseAddressExpression

Description: Returns the baseAddress expression defined on the given bank or localBank element.

— Returns: baseAddressExpression of type String - The baseAddress expression
— Input: bankOrLocalBankID of type String - Handle to a bank or localBank element

#### F.7.57.39 getBankBaseAddressID

Description: Returns the handle to the baseAddress defined on the given bank element.

— Returns: baseAddressID of type String - Handle to the baseAddress element
— Input: bankID of type String - Handle to a bank element

#### F.7.57.40 getBankBlockAndSubspaceElementIDs

Description: Returns the handles to all the banks, addressBlocks, or subspaceMaps defined on given bank or
localBank element.

— Returns: memoryElementIDs of type String - List of handles to the bank, addressBlock, or sub-

spaceMap elements

— Input: bankOrLocalBankID of type String - Handle to a bank or localBank element

#### F.7.57.41 getBankSubspaceMapIDs

Description: Returns the handles to all the subspaceMaps defined on the given bank element.

— Returns: subspaceMapIDs of type String - List of handles to the subspaceMap elements
— Input: bankID of type String - Handle to a bank element

#### F.7.57.42 getBankUsage

Description: Returns the usage defined on the given bank or localBank element.

— Returns: usage of type String - the bank usage
— Input: bankOrLocalBankID of type String - Handle to a bank or localBank element

#### F.7.57.43 getBankVolatility

Description: Returns the volatile value defined on the given bank or localBank element.

— Returns: volatile of type Boolean - The volatile value
— Input: bankOrLocalBankID of type String - Handle to a bank or localBank element

#### F.7.57.44 getMemoryMapAddressBlockIDs

Description: Returns the handles to all the addressBlocks defined on the given memoryMap element.

— Returns: addressBlockIDs of type String - List of handles to the addressBlock elements
— Input: memoryMapID of type String - Handle to a memoryMap element

#### F.7.57.45 getMemoryMapAddressUnitBits

Description: Returns the addressUnitBits defined on the given memoryMap or localMemoryMap element.

— Returns: addressUnitBits of type Long - The addressUnitBits value
— Input: memoryMapOrLocalMemoryMapID of type String - Handle to a memoryMap or

localMemoryMap element

#### F.7.57.46 getMemoryMapAddressUnitBitsExpression

Description: Returns the addressUnitBits expression defined on the given memoryMap or localMemoryMap
element.

— Returns: addressUnitBits of type String - The addressUnitBits expression
— Input: memoryMapOrLocalMemoryMapID of type String - Handle to a memoryMap or

localMemoryMap element

#### F.7.57.47 getMemoryMapAddressUnitBitsID

Description: Returns the handle to the addressUnitBits defined on the given memoryMap element.

— Returns: addressUnitBitsID of type String - Handle to the addressUnitBits element
— Input: memoryMapID of type String - Handle to a memoryMap element

#### F.7.57.48 getMemoryMapBankIDs

Description: Returns the handles to all the banks defined on the given memoryMap element.

— Returns: bankIDs of type String - List of handles to the bank elements
— Input: memoryMapID of type String - Handle to a memoryMap element

#### F.7.57.49 getMemoryMapElementIDs

Description: Returns the handles to all the banks, addressBlocks, or subspaceMaps defined on given
memoryMap or localMemoryMap element.

— Returns: memoryMapElementIDs of type String - List of handles to bank, addressBlock, or

subspaceMap elements

— Input: memoryMapOrLocalMemoryMapID of type String - Handle to a memoryMap or

localMemoryMap element

#### F.7.57.50 getMemoryMapElementType

Description: Returns the type of the given memoryMap element.

— Returns: memoryType of type String - The memory type (addressBlock, bank, or subSpaceMap)
— Input: memoryMapElementID of type String - Handle to a memoryMap element

#### F.7.57.51 getMemoryMapMemoryMapDefinitionRefByExternalTypeDefID

Description: Returns the handle to the externalTypeDefinitions referenced by the typeDefinitions attribute
of the memoryMapDefinitionRef defined on the given memoryMap element.

— Returns: externalTypeDefinitionsID of type String - Handle to the
externalTypeDefinitions element referenced by the typeDefinitions attribute

— Input: memoryMapID of type String - Handle to a memoryMap element

#### F.7.57.52 getMemoryMapMemoryMapDefinitionRefByID

Description: Returns the handle to the memoryMapDefinition (defined in the typeDefinitions root object)
referenced from the given memoryMap element.

— Returns: memoryMapDefinitionID of type String - Handle to the referenced

memoryMapDefinition

— Input: memoryMapID of type String - Handle to a memoryMap element

#### F.7.57.53 getMemoryMapMemoryMapDefinitionRefByName

Description: Returns the memoryMapDefinitionRef defined on the given memoryMap element.

— Returns: memoryMapDefinitionRef of type String - The referenced memoryMapDefinition
— Input: memoryMapID of type String - Handle to a memoryMap element

#### F.7.57.54 getMemoryMapMemoryMapDefinitionRefID

Description: Returns the handle to the memoryMapDefinitionRef defined on the given memoryMap
element.

— Returns: memoryMapDefinitionRefID of type String - Handle to the

memoryMapDefinitionRef element

— Input: memoryMapID of type String - Handle to a memoryMap element

#### F.7.57.55 getMemoryMapMemoryRemapIDs

Description: Returns the handles to all the memory Remaps defined on the given memoryMap element.

— Returns: memoryRemapIDs of type String - List of handles to the memoryRemap elements
— Input: memoryMapID of type String - Handle to a memoryMap element

#### F.7.57.56 getMemoryMapRemapIDs

Description: Returns the handles to all the memoryRemaps defined on the given memoryMap or
localMemoryMap element.

— Returns: memoryRemapIDs of type String - List of handles to memoryRemap elements
— Input: memoryMapOrLocalMemoryMapID of type String - Handle to a memoryMap or

localMemoryMap element

#### F.7.57.57 getMemoryMapShared

Description: Returns the shared value defined on the given memoryMap or localMemoryMap element.

— Returns: shared of type String - The shared value
— Input: memoryMapOrLocalMemoryMapID of type String - Handle to a memoryMap or a

localMemoryMap element

#### F.7.57.58 getMemoryMapSubspaceMapIDs

Description: Returns the handles to all the subSpaceMaps defined on the given memoryMap element.

— Returns: subSpaceMapID of type String - List of handles to the subSpaceMap elements
— Input: memoryMapID of type String - Handle to a memoryMap element

#### F.7.57.59 getMemoryRemapAddressBlockIDs

Description: Returns the handles to all the addressBlocks defined on the given memoryRemap element.

— Returns: addressBlockIDs of type String - List of handles to the addressBlock elements
— Input: memoryRemapID of type String - Handle to a memoryRemap element

#### F.7.57.60 getMemoryRemapBankIDs

Description: Returns the handles to all the banks defined on the given memoryRemap element.

— Returns: bankIDs of type String - List of handles to the bank elements
— Input: memoryRemapID of type String - Handle to a memoryRemap element

#### F.7.57.61 getMemoryRemapElementIDs

Description: Returns the handles to all the banks, addressBlocks, or subspaceMaps defined on the given
memoryRemap element.

— Returns: memoryMapElementIDs of type String - List of handles to bank, addressBlock, or

subspaceMap elements

— Input: memoryRemapID of type String - Handle to a memoryRemap element

#### F.7.57.62 getMemoryRemapModeRefByID

Description: Returns the modeID defined on the given memoryRemap element.

— Returns: modeID of type String - Handle to the referenced mode element
— Input: memoryRemapID of type String - Handle to an memoryRemap element
— Input: modeRef of type String - Handle to the referenced modeRef element

#### F.7.57.63 getMemoryRemapModeRefByNames

Description: Returns all the modeRefs defined on the given memoryRemap element.

— Returns: modeRefs of type String - List of the referenced modes
— Input: memoryRemapID of type String - Handle to a memoryRemap element

#### F.7.57.64 getMemoryRemapModeRefIDs

Description: Returns the handles to all the modeRefs defined on the given memoryMap element.

— Returns: modeRefIDs of type String - List of handles to the modeRef elements
— Input: memoryRemapID of type String - Handle to a memoryRemap element

#### F.7.57.65 getMemoryRemapRemapDefinitionRefByExternalTypeDefID

Description: Returns the handle to the externalTypeDefinitions referenced by the typeDefinitions attribute
of the remapDefinitionRef defined on the given memoryRemap element.

— Returns: remapDefinitionRefID of type String - Handle to the externalTypeDefinitions element referenced by the typeDefinitions attribute

— Input: memoryRemapID of type String - Handle to a memoryRemap element

#### F.7.57.66 getMemoryRemapRemapDefinitionRefByID

Description: Returns the handle to the remapDefinition referenced from the given memoryRemap element.

— Returns: remapDefinitionRefID of type String - Handle to the referenced remapDefinition element

— Input: memoryRemapID of type String - Handle to a memoryRemap element

#### F.7.57.67 getMemoryRemapRemapDefinitionRefByName

Description: Returns the remapDefinitionRef defined on the given memoryRemap element.

— Returns: remapDefinitionRef of type String - The remapDefinitionRef on a memoryRemap element

— Input: memoryRemapID of type String - Handle to a memoryMap element

#### F.7.57.68 getMemoryRemapRemapDefinitionRefID

Description: Returns the handle to the remapDefinitionRef defined on the given memoryRemap element.

— Returns: remapDefinitionRefID of type String - Handle to the remapDefinitionRef element
— Input: memoryRemapID of type String - Handle to a memoryRemap element

#### F.7.57.69 getMemoryRemapSubspaceMapIDs

Description: Returns the handles to all the subspaceMaps defined on the given memoryRemap element.

— Returns: subspaceMapID of type String - List of handles to the subspaceMap elements
— Input: memoryRemapID of type String - Handle to a memoryRemap element

#### F.7.57.70 getSubspaceMapBaseAddress

Description: Returns the baseAddress (resolved) value defined on the given subspaceMap.

— Returns: baseAddress of type Long - The base address value
— Input: subSpaceMapID of type String - Handle to a subspaceMap element

#### F.7.57.71 getSubspaceMapBaseAddressExpression

Description: Returns the baseAddress expression defined on the given subspaceMap.

— Returns: baseAddress of type String - The base address expression
— Input: subSpaceMapID of type String - Handle to a subspaceMap element

#### F.7.57.72 getSubspaceMapBaseAddressID

Description: Returns the handle to the baseAddress defined on the given subspaceMap element.

— Returns: baseAddressID of type String - Handle to the baseAddress element
— Input: subspaceMapID of type String - Handle to a subspaceMap element

#### F.7.57.73 getSubspaceMapSegmentRefByName

Description: Returns the segmentRef defined on the given subSpace element.

— Returns: segmentRef of type String - The referenced segment
— Input: subSpaceID of type String - Handle to a subSpace element

### F.7.58 Memory map (EXTENDED)

#### F.7.58.1 addAccessPolicyModeRef

Description: Adds a modeRef on an accessPolicy element.

— Returns: modeRefID of type String - Handle to the added modeRef
— Input: accessPolicyID of type String - Handle to an accessPolicy element
— Input: modeRef of type String - Name of the referenced access mode
— Input: priority of type Long - The non negative integer indication the priority

#### F.7.58.2 addAddressBlockRefIndex

Description: Adds an index to an addressBlockRef element.

— Returns: indexID of type String - Handle to the added index
— Input: addressBlockRefID of type String - Handle to an addressBlockRef element
— Input: value of type String - Index value

#### F.7.58.3 addAddressBlockRegister

Description: Adds a register with the given name, offset, and size, and a field with the given name, offset,
and width to the given addressBlock.

— Returns: registerID of type String - Handle to a new register element
— Input: addressBlockID of type String - Handle to an addressBlock element
— Input: name of type String - Register name
— Input: addressOffset of type String - Register address offset
— Input: size of type String - Register size
— Input: fieldName of type String - Field name
— Input: fieldOffset of type String - Field offset
— Input: fieldWidth of type String - Field width

#### F.7.58.4 addAddressBlockRegisterFile

Description: Adds a registerFile with the given name, addressOffset, and range to the given addressBlock
element.

— Returns: registerFileID of type String - Handle to a new registerFile element
— Input: addressBlockID of type String - Handle to an addressBlock element
— Input: name of type String - RegisterFile name
— Input: addressOffset of type String - RegisterFile address offset
— Input: range of type String - RegisterFile range

#### F.7.58.5 addAliasOfBankRef

Description: Adds an bankRef on an aliasOf element.

— Returns: bankRefID of type String - Handle to a bankRef element
— Input: aliasOfID of type String - Handle to an aliasOf element
— Input: bankRef of type String - Name of the referenced bank

#### F.7.58.6 addBankAccessPolicy

Description: Adds an accessPolicy on a bank element.

— Returns: accessPolicyID of type String - the accessPolicy identifier on a bank element
— Input: bankID of type String - Handle to a bank element
— Input: access of type String - Access enumerated value. Can be one of: read-only, write-only,

read-write, writeOnce, read-writeOnce or no-access

#### F.7.58.7 addBankAddressBlock

Description: Adds an addressBlock with the given name, range, and width to the given bank element.

— Returns: addressBlockID of type String - Handle to a new addressBlock element
— Input: bankID of type String - Handle to a bank element
— Input: name of type String - AddressBlock name
— Input: range of type String - AddressBlock range expression
— Input: width of type String - AddressBlock width expression

#### F.7.58.8 addBankBank

Description: Adds a bank to the given bank element

— Returns: bankID of type String - Handle to a bank identifier
— Input: bankID of type String - Handle to the given bank element
— Input: name of type String - Bank name
— Input: bankAlignment of type String - BankAlignment
— Input: addressBlockName of type String - The addressBlock name
— Input: addressBlockRange of type String - The addressRange name
— Input: addressBlockWidth of type String - The addressWidth name

#### F.7.58.9 addBankSubspaceMap

Description: Adds a subspaceMap to a bank element.

— Returns: subSpaceMap of type String - Handle to the added subSpaceMap
— Input: bankID of type String - Handle to a bank element
— Input: initiatorRef of type String - Name of the referenced initiator busInterface

#### F.7.58.10 addLocalMemoryMapBank

Description: Adds a bank to the given localMemoryMap element

— Returns: bankID of type String - Handle to a new bank element
— Input: localMemoryMapID of type String - Handle to a localMemoryMap element
— Input: name of type String - Bank name
— Input: bankAlignment of type String - The bankAlignment attribute
— Input: baseAddress of type String - Bank base address
— Input: addressBlockName of type String - Name of the default addressBlock
— Input: addressBlockRange of type String - Range expression of the default addressBlock
— Input: addressBlockWidth of type String - Width expression of the default addressBlock

#### F.7.58.11 addMemoryMapAddressBlock

Description: Adds an addressBlock with the given name, baseAddress, range, and width to the given
memoryMap element.

— Returns: addressBlockID of type String - Handle to a new addressBlock element
— Input: memoryMapID of type String - Handle to a memoryMap element
— Input: name of type String - AddressBlock name
— Input: baseAddress of type String - AddressBlock base address
— Input: range of type String - AddressBlock range
— Input: width of type String - AddressBlock width

#### F.7.58.12 addMemoryMapBank

Description: Adds a bank to the given memoryMap element

— Returns: bankID of type String - Handle to a new bank element
— Input: memoryMapID of type String - Handle to a memoryMap element
— Input: name of type String - Bank name
— Input: bankAlignment of type String - The bankAlignment attribute
— Input: baseAddress of type String - Bank base address
— Input: addressBlockName of type String - Name of the default addressBlock
— Input: addressBlockRange of type String - Range expression of the default addressBlock
— Input: addressBlockWidth of type String - Width expression of the default addressBlock

#### F.7.58.13 addMemoryMapMemoryRemap

Description: Adds a memoryRemap to memoryMap element.

— Returns: memoryRemapID of type String - Handle to a memoryRemap element
— Input: memoryMapID of type String - Handle to a memoryMap element
— Input: name of type String - Name of the memoryRemap
— Input: modeRef of type String - Name of the referenced mode
— Input: priority of type Long - Priority of the modeRef

#### F.7.58.14 addMemoryMapSubspaceMap

Description: Adds a subspaceMap with the given name, initiatorRef, and baseAddress to the given memory
map.

— Returns: subspaceMapID of type String - Handle to a new subspaceMap element
— Input: memoryMapID of type String - Handle to a memoryMap element
— Input: name of type String - SubspaceMap name
— Input: initiatorRef of type String - SubspaceMap initiatorRef
— Input: baseAddress of type String - SubspaceMap base address

#### F.7.58.15 addMemoryRemapAddressBlock

Description: Adds an addressBlock on a memoryRemap element.

— Returns: addressBlockID of type String - Handle to the added addressBlock
— Input: memoryRemapID of type String - Handle to a memoryRemap element

— Input: name of type String - AddressBlock name
— Input: baseAddress of type String - AddressBlock base address
— Input: range of type String - AddressBlock range
— Input: width of type String - AddressBlock width

#### F.7.58.16 addMemoryRemapBank

Description: Adds a memoryRemap to a memoryRemap element.

— Returns: bankID of type String - Handle to the added bank
— Input: memoryRemapID of type String - Handle to a memoryMap or memoryRemap element
— Input: name of type String - Bank name
— Input: baseAddress of type String - Bank base address
— Input: bankAlignment of type String - Bank alignment

#### F.7.58.17 addMemoryRemapModeRef

Description: Adds a modeRef to a memoryRemap element.

— Returns: modeRefID of type String - the modeRef identifier
— Input: memoryRemapID of type String - Handle to a memoryRemap element
— Input: modeRef of type String - Reference to mode
— Input: priority of type Long - The priority of the modeRef

#### F.7.58.18 addMemoryRemapSubspaceMap

Description: Adds a subspaceMap to a memoryRemapID element.

— Returns: subSpaceMapID of type String - Handle to the added subSpaceMap
— Input: memoryRemapID of type String - Handle to a memoryRemap Element
— Input: name of type String - Name of a subspaceMap
— Input: initiatorRef of type String - Name of the referenced initiator busInterface
— Input: baseAddress of type String - Value of the baseAddress

#### F.7.58.19 addRegisterFileRegisterFile

Description: Adds a registerFile with the given name, addressOffset, and range to the given registerFile
element.

— Returns: registerFileID of type String - Handle to the added registerFile
— Input: registerFileID of type String - Handle to a registerFile element
— Input: name of type String - RegisterFile name
— Input: addressOffset of type String - RegisterFile address offset
— Input: range of type String - RegisterFile range

#### F.7.58.20 removeAccessPolicyModeRef

Description: Removes the given modeRef from its containing accessPolicy element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: accessPolicyID of type String - Handle to an accessPolicy element
— Input: modeRef of type String - Name of the referenced access mode

#### F.7.58.21 removeAddressBlockArray

Description: Removes the array on the addressBlock element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressBlockID of type String - Handle to an addressBlock element

#### F.7.58.22 removeAddressBlockRefIndex

Description: Removes the given index from its containing addressBlockRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indexID of type String - Handle to the index element

#### F.7.58.23 removeAddressBlockRegister

Description: Removes the given register element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerID of type String - Handle to a register element

#### F.7.58.24 removeAddressBlockRegisterFile

Description: Removes the given registerFile element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerFileID of type String - Handle to a registerFile element

#### F.7.58.25 removeAddressBlockTypeIdentifier

Description: Removes the typeIdentifier from the given addressBlock element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressBlockID of type String - Handle to an addressBlock element

#### F.7.58.26 removeAddressBlockUsage

Description: Removes the usage from the given addressBlock element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressBlockID of type String - Handle to an addressBlock element

#### F.7.58.27 removeAddressBlockVolatility

Description: Removes the volatility from the given addressBlock element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressBlockID of type String - Handle to an addressBlock element

#### F.7.58.28 removeAliasOfAddressBlockRef

Description: Removes an addressBlockRef on an aliasOf element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: aliasOfID of type String - Handle to an aliasOf element

#### F.7.58.29 removeAliasOfAddressSpaceRef

Description: Removes the addressSpace Reference on an aliasOf element from registerField.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: aliasOfID of type String - Handle to an aliasOf element

#### F.7.58.30 removeAliasOfBankRef

Description: Removes the given bankRef from its containing aliasOf element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: bankrefID of type String - Handle to an bankRef element

#### F.7.58.31 removeAliasOfMemoryMapRef

Description: Removes the memoryMapRef on the aliasOf of a field on a register element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: aliasOfID of type String - Handle to an aliasOf element

#### F.7.58.32 removeBankAccessPolicy

Description: Removes the given accessPolicy from its containing bank element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: accessPolicyID of type String - Handle to an accessPolicy element

#### F.7.58.33 removeBankAddressBlock

Description: Removes an addressBlock with the given addressBlockID.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressBlockID of type String - Handle to an addressBlock element

#### F.7.58.34 removeBankBank

Description: Removes the given bank element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: bankOrLocalBankID of type String - Handle to bank or localBank element

#### F.7.58.35 removeBankSubspaceMap

Description: Removes the given subspaceMap from its containing bank element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: subspaceMapID of type String - Handle to a subspaceMap element

#### F.7.58.36 removeBankUsage

Description: Removes usage from the given bank element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: bankID of type String - Handle to bank

#### F.7.58.37 removeBankVolatility

Description: Removes volatility from the given bank element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: bankID of type String - Handle to a bank element

#### F.7.58.38 removeMemoryMapAddressBlock

Description: Removes the given addressBlock element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressBlockID of type String - Handle to an addressBlock element

#### F.7.58.39 removeMemoryMapBank

Description: Removes the given bank element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: bankOrLocalBankID of type String - Handle to bank or localBank element

#### F.7.58.40 removeMemoryMapMemoryRemap

Description: Removes the given memoryRemap from its containing memoryMap element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: memoryRemapID of type String - Handle to a memoryRemap element

#### F.7.58.41 removeMemoryMapShared

Description: Removes the shared from the given memoryMap element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: memoryMapID of type String - Handle to a memoryMap element

#### F.7.58.42 removeMemoryMapSubspaceMap

Description: Removes the given subspaceMap element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: subSpaceMapID of type String - Handle to a subspaceMap element

#### F.7.58.43 removeMemoryRemapBank

Description: Removes the given bank from a memoryRemap element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: bankID of type String - Handle to a bank element

#### F.7.58.44 removeMemoryRemapMapAddressBlock

Description: Removes the given addressBlock from its containing memoryRemap element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressBlockID of type String - Handle to an addressBlock element

#### F.7.58.45 removeMemoryRemapModeRef

Description: Removes the given modeRef from its containing memoryRemap element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: modeRefID of type String - Handle to a modeRef element

#### F.7.58.46 removeMemoryRemapSubspaceMap

Description: Removes the given subspaceMap from its containing memoryRemap element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: subspaceMapID of type String - Handle to subspaceMap element

#### F.7.58.47 removeRegisterArray

Description: Removes the array on the given register.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerID of type String - Handle to a register element

#### F.7.58.48 removeRegisterFileArray

Description: Removes the array on the register.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerFileID of type String - Handle to a registerFile element

#### F.7.58.49 setAddressBlockAddressBlockDefinitionRef

Description: Sets the addressBlockDefinitionRef with his value and typeDefinitions.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressBlockID of type String - Handle to an addressBlock element
— Input: value of type String - Name of the referenced addresBlockDefinition in an external

typeDefinitions

— Input: typeDefinitions of type String - Name of the component externalTypeDefinitions

#### F.7.58.50 setAddressBlockArray

Description: Sets the array on the addressBlock element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressBlockID of type String - Handle to an addressBlock element
— Input: dim of type String - The dim value

#### F.7.58.51 setAddressBlockBaseAddress

Description: Sets the baseAddress value of the given addressBlock

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressBlockID of type String - Handle to an addressBlock
— Input: baseAddress of type String - Expression of the base address

#### F.7.58.52 setAddressBlockDefinitionRef

Description: Sets the value field of the given addressblock definition ref of an addressblock.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressBlockDefinitionRefID of type String - Handle to an

addressBlockDefinitionRef

— Input: value of type String - Handle to the new value

#### F.7.58.53 setAddressBlockRange

Description: Sets the range with the given value for the given addressBlock element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressBlockID of type String - Handle to an addressBlock element
— Input: range of type String - The addressBlock range

#### F.7.58.54 setAddressBlockTypeIdentifier

Description: Sets the typeIdentifier with the given value for the given addressBlock element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressBlockID of type String - Handle to an addressBlock element
— Input: typeIdentifier of type String - The addressBlock typeIdentifier

#### F.7.58.55 setAddressBlockUsage

Description: Sets the usage with the given value for the given addressBlock element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressBlockID of type String - Handle to an addressBlock element
— Input: usage of type String - The addressBlock usage

#### F.7.58.56 setAddressBlockVolatility

Description: Sets the volatility with the given value for the given addressBlock element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressBlockID of type String - Handle to an addressBlock element
— Input: _volatile of type Boolean - The addressBlock volatility

#### F.7.58.57 setAddressBlockWidth

Description: Sets the width of the given addressBlock element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressBlockID of type String - Handle to an addressBlock element
— Input: width of type String - Width expression to be set

#### F.7.58.58 setAliasOfAddressBlockRef

Description: Sets an addressBlockRef on an aliasOf element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: aliasOfID of type String - Handle to an aliasOf element

— Input: addressBlockRef of type String - Name of the referenced addressBlock

#### F.7.58.59 setAliasOfAddressSpaceRef

Description: Sets the addressSpace Reference on the given aliasOf element from registerField.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: aliasOfID of type String - Handle to an aliasOf element
— Input: addressSpaceRef of type String - Name of the referenced addressSpace

#### F.7.58.60 setAliasOfMemoryMapRef

Description: Sets the memoryMapRef on the aliasOf of a field on a register element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: aliasOfID of type String - Handle to an aliasOf element
— Input: memoryMapRef of type String - Name of the referenced memoryMap

#### F.7.58.61 setAliasOfMemoryRemapRef

Description: Sets an memoryRemapRef on an aliasOf element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: aliasOfID of type String - Handle to an aliasOf element
— Input: memoryRemapRef of type String - Name of the referenced memoryRemap

#### F.7.58.62 setBankBankDefinitionRef

Description: Sets the bankDefinitionRef on a bank element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: bankID of type String - Handle to a bank element
— Input: value of type String - Name of the referenced bankFileDefinition in an

externalTypeDefinitions

— Input: typeDefinitions of type String - Name of the component externalTypeDefinitions

#### F.7.58.63 setBankBaseAddress

Description: Sets the baseAddress value of the given bank and returns an identifier to an addressBlock.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: bankID of type String - Handle to an bank
— Input: baseAddress of type String - Expression of the base address

#### F.7.58.64 setBankUsage

Description: Sets usage with the given value for the given bank element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: bankID of type String - Handle to bank or localBank element
— Input: usage of type String - Bank usage

#### F.7.58.65 setBankVolatility

Description: Sets volatility with the given value for the given bank element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: bankOrLocalBankID of type String - Handle to bank or localBank element
— Input: volatile of type Boolean - Bank volatility

#### F.7.58.66 setBroadcastToAddressSpaceRef

Description: Sets the addressSpace Reference on the given broadcastTo element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: broadcastToID of type String - Handle to an broadcastTo element
— Input: addressSpaceRef of type String - Name of the referenced addressSpace

#### F.7.58.67 setMemoryMapMemoryMapDefinitionRef

Description: Sets a Value to MemoryMapDefintionRef.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: memoryMapID of type String - Handle to a memoryMap
— Input: value of type String - Name of the referenced memoryMapDefinition in an

externalTypeDefinitions

— Input: typeDefinitions of type String - Name of the component externalTypeDefinitions

#### F.7.58.68 setMemoryMapShared

Description: Sets the shared flag with the given value to the given memoryMap element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: memoryMapID of type String - Handle to a memoryMap element
— Input: shared of type String - MemoryMap shared enumeration value

#### F.7.58.69 setMemoryRemapRemapDefinitionRef

Description: Sets the remapDefinitionRef on a memoryRemap element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: memoryRemapID of type String - Handle to a memoryMap element
— Input: value of type String - Name of the referenced remapDefinition in an

externalTypeDefinitions

— Input: typeDefinitions of type String - Name of the component externalTypeDefinitions

#### F.7.58.70 setRegisterArray

Description: Sets the array on the register.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerID of type String - Handle to a register element
— Input: dimValue of type String - the dim value to set on the array

#### F.7.58.71 setRegisterFieldArray

Description: Sets the array on the given field of a register.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerFieldID of type String - Handle to a field element on a register

— Input: value of type String - Dimension of the array

#### F.7.58.72 setRegisterFieldBitOffset

Description: Sets the bitOffset expression on the given field of a register.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerFieldID of type String - Handle to a field element on a register
— Input: bitOffset of type String - The bitOffset expression

#### F.7.58.73 setRegisterFileArray

Description: Sets the array on the register.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerFileID of type String - Handle to a registerFile element
— Input: dimValue of type String - The dim value to set on the array

#### F.7.58.74 setSubSpaceMapBaseAddress

Description: Sets the baseAddress value of the given subSpaceMap

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: subSpaceMapID of type String - Handle to an subSpaceMap
— Input: baseAddress of type String - Expression of the base address

### F.7.59 Miscellaneous (BASE)

#### F.7.59.1 getArgumentValue

Description: Returns the value defined on the given fileSet function argument element.

— Returns: value of type String - The value of the value element
— Input: argumentID of type String - Handle to an argument element

#### F.7.59.2 getArgumentValueExpression

Description: Returns the expression of the value defined on the given fileSet function argument element.

— Returns: expression of type String - The expression of the value element
— Input: argumentID of type String - Handle to an argument element

#### F.7.59.3 getArgumentValueID

Description: Returns the handle to the value defined on the given fileSet function argument element.

— Returns: valueID of type String - Handle to the value element
— Input: argumentID of type String - Handle to an argument element

#### F.7.59.4 getBooleanValue

Description: Returns the boolean value of the given element.

— Returns: value of type Boolean - The value of the given element
— Input: elementID of type String - Handle to an IP-XACT element

#### F.7.59.5 getDefineValue

Description: Returns the value defined on the given fileSet define element.

— Returns: value of type String - The value of the value element
— Input: defineID of type String - Handle to a define element

#### F.7.59.6 getDefineValueExpression

Description: Returns the expression on a define element.

— Returns: expression of type String - The expression of the value element
— Input: defineID of type String - Handle to a define element

#### F.7.59.7 getDefineValueID

Description: Returns the handle to the value defined on the given fileSet define element.

— Returns: valueID of type String - Handle to the value element
— Input: defineID of type String - Handle to a define element

#### F.7.59.8 getExpression

Description: Returns the expression defined on the given expressionContainer element.

— Returns: expression of type String - The expression (not evaluated)
— Input: expressionID of type String - Handle to an expression element

#### F.7.59.9 getExpressionIntValue

Description: Returns the value of the given expression.

— Returns: expression of type Long - The value of the expression (not evaluated)
— Input: expressionID of type String - Handle to an expression

#### F.7.59.10 getExpressionValue

Description: Returns the value of the given expression.

— Returns: expression of type String - The value of the expression (evaluated)
— Input: expressionID of type String - Handle to an expression element

#### F.7.59.11 getGroup

Description: Returns the name of the given group element.

— Returns: name of type String - The group name
— Input: groupID of type String - Handle to a group element

#### F.7.59.12 getPartSelectIndexIDs

Description: Returns the handles to all the indexes defined on the given partSelect element.

— Returns: indexID of type String - List of handles to the index elements
— Input: partSelectID of type String - Handle to a partSelect element

#### F.7.59.13 getPartSelectIndices

Description: Returns all the indices values defined on the given partSelect element.

— Returns: indices of type Long - List of the indices values
— Input: partSelectID of type String - Handle to a partSelect

#### F.7.59.14 getPartSelectIndicesExpression

Description: Returns all the indices expressions defined on the given partSelect element.

— Returns: indicesExpression of type String - List of the indices expressions
— Input: partSelectID of type String - Handle to a partSelect

#### F.7.59.15 getPartSelectRange

Description: Returns the range (resolved) value defined on the given partSelect element.

— Returns: range of type Long - Array of two range values: left and right
— Input: partSelectID of type String - Handle to a partSelect element

#### F.7.59.16 getPartSelectRangeExpression

Description: Returns the range expression defined on the given partSelect element.

— Returns: range of type String - Array of two range expressions: left and right
— Input: partSelectID of type String - Handle to a partSelect element

#### F.7.59.17 getPartSelectRangeLeftID

Description: Returns the handle to the left range defined on the given partSelect element.

— Returns: leftRangeID of type String - Handle to the left range
— Input: partSelectID of type String - Handle to a partSelect element

#### F.7.59.18 getPartSelectRangeRightID

Description: Returns the handle to the right range defined on the given partSelect element.

— Returns: rightRangeID of type String - Handle to the right range
— Input: partSelectID of type String - Handle to a partSelect element

#### F.7.59.19 getValue

Description: Returns the string value of the given element.

— Returns: value of type String - The value of the given element
— Input: elementID of type String - Handle to an IP-XACT element

#### F.7.59.20 getXML

Description: Returns the XML fragment.

— Returns: xmlString of type String - The XML fragment
— Input: elementID of type String - IP-XACT XML element

### F.7.60 Miscellaneous (EXTENDED)

#### F.7.60.1 addPartSelectIndex

Description: Adds an index on a partSelect element.

— Returns: indexID of type String - the index identifier
— Input: partSelectID of type String - Handle to a partSelect
— Input: value of type String - the index value

#### F.7.60.2 end

Description: Terminates the connection to the DE.

— Returns: status of type Long - Status indicator from the DE. Non-Zero implies an error
— Input: genStatus of type Long - Status indicator from the generator. Non-zero implies an error
— Input: message of type String - Message that the DE may display to the user

#### F.7.60.3 init

Description: API initialization function. Must be called before any other TGI call.

— Returns: status of type Boolean - True if the call is successful False otherwise
— Input: apiVersion of type String - The API version with which the generator is defined to work
— Input: failureMode of type String - Compatibility failure mode (fail, error or warning)
— Input: message of type String - Message that the DE may display to the user

#### F.7.60.4 isSetElement

Description: Checks if the given element is set or not.

— Returns: isSet of type Boolean - True if the element is defined; False otherwise
— Input: elementContainerID of type String - Handle to the parent of the element to check
— Input: elementName of type String - Name of the element

#### F.7.60.5 message

Description: Sends the given message level and message text to the DE.

— Returns: status of type Boolean - True if the call is successful, False otherwise
— Input: severity of type String - message level
— Input: message of type String - message text

#### F.7.60.6 registerCatalogVLNVs

Description: Registers all the VLNVs defined in the given catalog.

— Returns: status of type Boolean - True if the call is successful, False otherwise
— Input: catalogID of type String - Catalog who's VLNVs are to be registered

#### F.7.60.7 registerVLNV

Description: Registers the VLNV contained in the given file, possibly replacing an existing VLNV.

— Returns: status of type Boolean - True if the call is successful, False otherwise
— Input: fileName of type String - Location of file that is to be registered

— Input: replace of type Boolean - Replace existing VLNV with new content

#### F.7.60.8 removePartSelectIndex

Description: Removes the given index from its containing a partSelect indices element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indexID of type String - The identifier of an index element

#### F.7.60.9 resolveExpression

Description: Resolves any expression for given parameter and value pairs.

— Returns: expression of type String - The resolved expression
— Input: expression of type String - The expression to solve
— Input: values of type String[] - Name and value pairs formatted as name = value, where value

must be a constant.

#### F.7.60.10 save

Description: Save all edits done in generator to DE; document must be valid.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)

#### F.7.60.11 setArgumentValue

Description: Sets the value on an argument element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: argumentID of type String - Handle to an argument element
— Input: value of type String - The value to set on the argument

#### F.7.60.12 setBooleanValue

Description: Sets the boolean value on the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an IP-XACT element
— Input: value of type Boolean - The value to be set

#### F.7.60.13 setDefineValue

Description: Sets the value on a define element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: argumentID of type String - Handle to an argument element
— Input: value of type String - The value to set on the argument

#### F.7.60.14 setExpressionValue

Description: Sets the value to the given expression

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: expressionID of type String - Handle to an expression
— Input: value of type String - New value expression.

#### F.7.60.15 setPartSelectRange

Description: Sets the PartSelect Range field.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: partSelectID of type String - Handle to a partSelect element
— Input: left of type String - Left value of the range
— Input: right of type String - Right value of the range

#### F.7.60.16 setValue

Description: Sets the string value on the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an IP-XACT element
— Input: value of type String - The value to be set

#### F.7.60.17 removePartSelectRange

Description: Remove the range of a partSelect element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: partSelectID of type String - Handle to partSelect

#### F.7.60.18 unregisterCatalogVLNVs

Description: Unregister all the VLNVs in the given catalog.

— Returns: status of type Boolean - True if the call is successful, False otherwise
— Input: catalogID of type String - Catalog which VLNVs are to be unregistered

#### F.7.60.19 unregisterVLNV

Description: Unregisters the given VLNV.

— Returns: status of type Boolean - True if the call is successful, False otherwise
— Input: VLNV of type String[] - VLNV that is to be unregistered

### F.7.61 Module parameter (BASE)

#### F.7.61.1 getModuleParameterIDs

Description: Returns the handles to all the module or type parameters defined on the given element.

— Returns: moduleOrTypeParameterIDs of type String - List of handles to module or type

parameter elements

— Input: moduleOrTypeParameterContainerElementID of type String - Handle to an ele-

ment that has moduleOrTypeParameter elements

#### F.7.61.2 getModuleParameterValue

Description: Returns the value defined on the given module or type parameter element.

— Returns: value of type String - The parameter value
— Input: moduleParameterID of type String - Handle to a module or type parameter element

#### F.7.61.3 getModuleParameterValueExpression

Description: Returns expression defined on the given module or type parameter element.

— Returns: expression of type String - The parameter expression
— Input: moduleParameterID of type String - Handle to a module or type parameter element

### F.7.62 Module parameter (EXTENDED)

#### F.7.62.1 addModuleParameter

Description: Adds a moduleOrTypeParameter with the given name and given value to the given element.

— Returns: moduleOrTypeParameterID of type String - Handle to a new

moduleOrTypeParameter

— Input: moduleOrTypeParameterContainerElementID of type String - Handle to an element that has moduleOrTypeParameter elements

— Input: name of type String - The moduleOrTypeParameter name
— Input: expression of type String - The moduleOrTypeParameter expression

#### F.7.62.2 removeModuleParameter

Description: Removes the given moduleOrTypeParameter.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: moduleParameterID of type String - Handle to a moduleOrTypeParameter element

#### F.7.62.3 setModuleParameterValue

Description: Sets the value of the given moduleOrTypeParameter.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: moduleOrTypeParameterID of type String - Handle to a moduleOrTypeParameter element

— Input: expression of type String - moduleOrTypeParameter expression

### F.7.63 Name group (BASE)

#### F.7.63.1 getDescription

Description: Returns the description defined on the given element.

— Returns: description of type String - The description of the given element
— Input: elementID of type String - Handle to an element that has a nameGroup

#### F.7.63.2 getDisplayName

Description: Returns the display name defined on the given element.

— Returns: displayName of type String - The display name of the given element
— Input: elementID of type String - Handle to an element that has a nameGroup

#### F.7.63.3 getName

Description: Returns the name defined on the given element.

— Returns: name of type String - The name of the given element
— Input: elementID of type String - Handle to an element that has a nameGroup

#### F.7.63.4 getShortDescription

Description: Returns the short description of the given element. (Unresolved).

— Returns: shortDescription of type String - The short description
— Input: elementID of type String - Handle to a name group element

### F.7.64 Name group (EXTENDED)

#### F.7.64.1 removeDescription

Description: Removes the given description from its containing described element; fails if description is not
already set.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element that has a nameGroup

#### F.7.64.2 removeDisplayName

Description: Removes the given displayName from its containing groupName element; fails if displayName
is not already set.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element that has a nameGroup

#### F.7.64.3 removeName

Description: Removes the name of the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element that has a nameGroup

#### F.7.64.4 removeShortDescription

Description: Removes the given shortDescription from its containing groupName element; fails if
shortDescription is not already set.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element that has a nameGroup

#### F.7.64.5 setDescription

Description: Sets given description for the given element; fails if description is not already set.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element that has a nameGroup
— Input: description of type String - New description

#### F.7.64.6 setDisplayName

Description: Sets given display name for the given element; fails if display name is not already set.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)

— Input: elementID of type String - Handle to an element that has a nameGroup
— Input: displayName of type String - New display name

#### F.7.64.7 setName

Description: Sets the name of the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to an element that has a nameGroup
— Input: name of type String - New name

#### F.7.64.8 setShortDescription

Description: Sets the short description.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: elementID of type String - Handle to a nameGroup
— Input: shortDescription of type String - Handle to the new value

### F.7.65 Parameter (BASE)

#### F.7.65.1 getModuleParameterDataTypeDefinitionRefByID

Description: Returns the handle to the file referenced from the given moduleParameterType element.

— Returns: fileID of type String - Handle to the referenced file element
— Input: moduleParameterTypeID of type String - Handle to a moduleParameterType element

#### F.7.65.2 getParameterChoiceRefByName

Description: Returns the choice referenced from the given parameter element.

— Returns: choiceRef of type String - The referenced choice
— Input: parameterBaseTypeID of type String - Handle to a parameter element

#### F.7.65.3 getParameterIDFromReferenceID

Description: Returns the handle to the parameter element from the given component and reference elements.

— Returns: parameterID of type String - Handle to the parameter element
— Input: parametizedID of type String - Handle to an element containing parameters
— Input: referenceID of type String - Handle to a referenceID element

#### F.7.65.4 getParameterIDs

Description: Returns the handles to all the parameters defined on the given element.

— Returns: parameterIDs of type String - List of handles to parameter elements
— Input: parameterContainerElementID of type String - Handle to an element that has

parameter elements

#### F.7.65.5 getParameterNameFromReferenceID

Description: Returns the parameter name from the given component and reference elements.

— Returns: parameterName of type String - The parameter name

— Input: parametizedID of type String - Handle to an element containing parameters
— Input: referenceID of type String - Handle to a referenceID element

#### F.7.65.6 getParameterValue

Description: Returns the value defined on the given parameter element.

— Returns: value of type String - The parameter value
— Input: parameterID of type String - Handle to a parameter element

#### F.7.65.7 getParameterValueExpression

Description: Returns the expression defined on the given parameter element.

— Returns: expression of type String - The parameter expression
— Input: parameterID of type String - Handle to a parameter element

#### F.7.65.8 getParameterValueID

Description: Returns the handle expression of the given parameter element.

— Returns: parameterValueID of type String - Handle to the parameterValue element
— Input: parameterID of type String - Handle to a parameter element

### F.7.66 Parameter (EXTENDED)

#### F.7.66.1 addParameter

Description: Adds a parameter with the given name and given value to the given element.

— Returns: parameterID of type String - Handle to a new parameter
— Input: parameterContainerElementID of type String - Handle to an element that has

parameter elements

— Input: name of type String - Parameter name
— Input: expression of type String - Parameter expression

#### F.7.66.2 removeConfigGroupsAttribute

Description: Removes a configGroups of the given parameter.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: parameterID of type String - Handle to a parameter

#### F.7.66.3 removeParameter

Description: Removes the given parameter.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: parameterID of type String - Handle to a parameter element

#### F.7.66.4 setParameterValue

Description: Sets the value of the given parameter.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: parameterID of type String - Handle to a parameter element

— Input: expression of type String - Parameter expression

### F.7.67 Port (BASE)

#### F.7.67.1 getAccessPortAccessType

Description: Returns the accessType defined on the given access element.

— Returns: accessType of type String - The port access type
— Input: accessID of type String - Handle to an access element

#### F.7.67.2 getDomainTypeDefTypeDefinitionIDs

Description: Returns the handles to all the typeDefinitions defined on the given domainTypeDef element.

— Returns: typeDefinitionIDs of type String - List of handles to the typeDefinition elements
— Input: domainTypeDefID of type String - Handle to a domainTypeDef element

#### F.7.67.3 getDomainTypeDefTypeDefinitions

Description: Returns the typeDefinitions defined on the given domainTypeDef element.

— Returns: typeDefinitions of type String - List of typeDefinitions
— Input: domainTypeDefID of type String - Handle to a domainTypeDef element

#### F.7.67.4 getDomainTypeDefTypeName

Description: Returns the typeName defined on the given domainTypeDef element.

— Returns: typeName of type String - The type name
— Input: domainTypeDefID of type String - Handle to a domainTypeDef element

#### F.7.67.5 getDomainTypeDefTypeNameID

Description: Returns the handle to the typeName defined on the given domainTypeDef element.

— Returns: typeNameID of type String - Handle to the typeName element
— Input: domainTypeDefID of type String - Handle to a domainTypeDef element

#### F.7.67.6 getDomainTypeDefViewIDs

Description: Returns the handles to all the views defined on the given domainTypeDef element.

— Returns: viewIDs of type String - List of handles to the view elements
— Input: domainTypeDefID of type String - Handle to a domainTypeDef element

#### F.7.67.7 getDomainTypeDefViewRefIDs

Description: Returns the handles to all the viewRefs defined on the given domainTypeDef element.

— Returns: viewRefIDs of type String - List of handles to the viewRef elements
— Input: domainTypeDefID of type String - Handle to a domainTypeDef element

#### F.7.67.8 getDomainTypeDefViewRefs

Description: Returns all the viewRefs defined on the given domainTypeDef element.

— Returns: viewRefs of type String - List of the referenced views
— Input: domainTypeDefID of type String - Handle to a domainTypeDef element

#### F.7.67.9 getFieldDefinitionAccessPoliciesIDs

Description: Returns the handles to all the AccessPolicies defined on the given fieldDefinition element.

— Returns: accessPoliciesIDs of type String - List of handles to the accessPolicies elements
— Input: fieldDefinitionID of type String - Handle to a fieldDefinition element

#### F.7.67.10 getFieldMapFieldSliceID

Description: Returns the handle to fieldSlice defined on the given fieldMap element.

— Returns: fieldSliceID of type String - Handle to the fieldSlice element
— Input: fieldMapID of type String - Handle to a fieldMap element

#### F.7.67.11 getFieldMapModeRefByID

Description: Returns the handle to the mode referenced from the given fieldMap element.

— Returns: modeID of type String - Handle to the referenced mode element
— Input: fieldMapID of type String - Handle to a fieldMap element
— Input: modeRef of type String - The referenced mode

#### F.7.67.12 getFieldMapModeRefByNames

Description: Returns all the modeRefs defined on the given fieldMap element.

— Returns: modeRefs of type String - List of the referenced modes
— Input: fieldMapID of type String - Handle to a fieldMap element

#### F.7.67.13 getFieldMapModeRefIDs

Description: Returns the handles to all the modeRef defined on the given fieldMap element

— Returns: modeRefIDs of type String - Handles to modeRefs elements
— Input: fieldMapID of type String - Handle to a fieldMap

#### F.7.67.14 getFieldMapModeRefs

Description: Returns all the modeRefs defined on the given fieldMap element.

— Returns: modeRefs of type String - List of the referenced modes
— Input: fieldMapID of type String - Handle to a fieldMap element

#### F.7.67.15 getFieldMapPartSelectID

Description: Returns the handle to the partSelect defined on the given fieldMap element.

— Returns: partSelectID of type String - Handle to the partSelect element
— Input: fieldMapID of type String - Handle to a fieldMap element

#### F.7.67.16 getFieldMapSubPortReferenceIDs

Description: Returns the handles to all the subPortReferences defined on the given fieldMap element.

— Returns: subPortReferenceID of type String - List of handles to the subPortReference elements

— Input: fieldMapID of type String - Handle to a fieldMap element

#### F.7.67.17 getPayloadExtension

Description: Returns the name of the payload extension defined on the given payload element.

— Returns: extension of type String - The payload extension name
— Input: payloadID of type String - Handle to a protocol payload element

#### F.7.67.18 getPayloadExtensionID

Description: Returns the handle to the payload extension defined on the given payload element.

— Returns: extensionID of type String - Handle to the payload extension element
— Input: payloadID of type String - Handle to a protocol payload element

#### F.7.67.19 getPayloadType

Description: Returns the type defined on the given payload element.

— Returns: type of type String - The payload type
— Input: payloadID of type String - Handle to a payload element

#### F.7.67.20 getPortAccessID

Description: Returns the handle to the access defined on the given port element.

— Returns: portAccessID of type String - Handle to the portAccess element
— Input: portID of type String - Handle to a port element

#### F.7.67.21 getPortDomainTypeDefIDs

Description: Returns the handles to all the domainTypeDef defined on the given port wire element.

— Returns: domainTypeDefIDs of type String - List of handles to domainTypeDef elements
— Input: wireID of type String - Handle to a port wire element

#### F.7.67.22 getPortFieldMapIDs

Description: Returns the handles to all the fieldMap defined on the given port element.

— Returns: fieldMapIDs of type String - List of handles to fieldMap elements
— Input: portID of type String - Handle to a mode element

#### F.7.67.23 getPortSignalTypeDefIDs

Description: Returns the handles to all the signalTypeDef defined on the given port wire element.

— Returns: signalTypeDefIDs of type String - List of handles to signalTypeDef elements
— Input: wireID of type String - Handle to a port wire element

#### F.7.67.24 getPortStructuredID

Description: Returns the handle to the structured element defined on the given port element.

— Returns: structuredID of type String - Handle to the structured element

— Input: portID of type String - Handle to a port element

#### F.7.67.25 getPortStructuredInterfaceID

Description: Returns the handle to the interface

— Returns: interfaceID of type String - Handle to an interface element
— Input: structuredID of type String - Handle to a port structured element

#### F.7.67.26 getPortStructuredStructID

Description: Returns the handle to the struct defined on the given structuredPort element.

— Returns: structID of type String - Handle to the struct element
— Input: structuredID of type String - Handle to a port structured

#### F.7.67.27 getPortStructuredStructPortTypeDefIDs

Description: Returns the handles to all the structPortTypeDef typeDefinitions defined on the given port
structured element.

— Returns: structPortTypeDefIDs of type String - List of handles to the structPortTypeDef elements

— Input: structuredID of type String - Handle to a port structured element

#### F.7.67.28 getPortStructuredSubPortIDs

Description: Returns the handles to all the subPorts defined on the given port structured element.

— Returns: subPortIDs of type String - List of handles to the subPort elements
— Input: structuredID of type String - Handle to a port structured element

#### F.7.67.29 getPortStructuredUnionID

Description: Returns the handle to the union element defined on the given structuredPort element.

— Returns: unionID of type String - Handle to the union element
— Input: structuredID of type String - Handle to a port structured element

#### F.7.67.30 getPortStructuredVectorIDs

Description: Returns the handles to all the vectors defined on the given port structured element.

— Returns: vectorIDs of type String - List of handles to the vector elements
— Input: structuredID of type String - Handle to a port structured element

#### F.7.67.31 getPortStyle

Description: Returns the style (wire, transactional or structured) of the given port element.

— Returns: style of type String - The port style (wire or transactional or structured)
— Input: portID of type String - Handle to a port element

#### F.7.67.32 getPortTransactionalBusWidth

Description: Returns the busWidth value defined on the given port element.

— Returns: width of type Long - The busWidth value

— Input: transactionalID of type String - Handle to a port transactional element

#### F.7.67.33 getPortTransactionalBusWidthExpression

Description: Returns the busWidth expression defined on the given port element.

— Returns: widthExpression of type String - The busWidth expression
— Input: transactionalID of type String - Handle to a port transactional element

#### F.7.67.34 getPortTransactionalBusWidthID

Description: Returns the handle to the busWidth defined on the given port transactional element.

— Returns: widthID of type String - Handle to the busWidth element
— Input: transactionalID of type String - Handle to a port transactional element

#### F.7.67.35 getPortTransactionalID

Description: Returns the handle to the transactional element defined on the given port element.

— Returns: transactionalID of type String - Handle to the transactional element
— Input: portID of type String - Handle to a port element

#### F.7.67.36 getPortTransactionalInitiative

Description: Returns the initiative defined on the given port transactional element.

— Returns: initiative of type String - The port initiative
— Input: transactionalID of type String - Handle to a port transactional element

#### F.7.67.37 getPortTransactionalKind

Description: Returns the kind defined on the given port transactional element.

— Returns: kind of type String - The port kind
— Input: transactionalID of type String - Handle to a port transactional element

#### F.7.67.38 getPortTransactionalKindID

Description: Returns the handle to the kind defined on the given port transactional element.

— Returns: kind of type String - Handle to the kind element
— Input: transactionalID of type String - Handle to a port transactional element

#### F.7.67.39 getPortTransactionalMaxConnections

Description: Returns the maxConnections defined on the given port element.

— Returns: value of type Long - The maximum number of connections allowed on the port
— Input: transactionalID of type String - Handle to a port transactional element

#### F.7.67.40 getPortTransactionalMaxConnectionsExpression

Description: Returns the maxConnections expression defined on the given port element.

— Returns: valueExpression of type String - The maxConnections expression
— Input: transactionalID of type String - Handle to a port transactional element

#### F.7.67.41 getPortTransactionalMaxConnectionsID

Description: Returns the handle to the maxConnections defined on the given port transactional element.

— Returns: maxConnectionsID of type String - Handle to the maximum number of connections

allowed on this port

— Input: portID of type String - Handle to a port transactional element

#### F.7.67.42 getPortTransactionalMinConnections

Description: Returns the minConnections defined on the given port element.

— Returns: value of type Long - The minimum number of connections allowed on the port
— Input: transactionalID of type String - Handle to a port transactional element

#### F.7.67.43 getPortTransactionalMinConnectionsExpression

Description: Returns the minConnections expression defined on the given port element.

— Returns: valueExpression of type String - The minConnections expression
— Input: transactionalID of type String - Handle to a port transactional element

#### F.7.67.44 getPortTransactionalMinConnectionsID

Description: Returns the handle to the minConnections defined on the given port transactional element.

— Returns: minConnectionsID of type String - Handle to the minimum number of connections

required on this port

— Input: transactionalID of type String - Handle to a port transactional element

#### F.7.67.45 getPortTransactionalProtocolID

Description: Returns the handle to the protocol defined on the given port transactional element.

— Returns: ProtocolID of type String - Handle to the protocol element
— Input: transactionalID of type String - Handle to a port transactional element

#### F.7.67.46 getPortTransactionalQualifierID

Description: Returns the handle to the qualifier defined on the given component port transactional element.

— Returns: qualifierID of type String - Handle to the qualifier element
— Input: transactionalID of type String - Handle to port transactional

#### F.7.67.47 getPortTransactionalTransTypeDefIDs

Description: Returns the handles to all the transTypeDefs defined on the given port element.

— Returns: transTypeDefIDs of type String - List of handles to transTypeDef elements
— Input: transactionalID of type String - Handle to a port transactional element

#### F.7.67.48 getPortWireConstraintSetIDs

Description: Returns the handles to all the constraintSet elements defined on given port wire element.

— Returns: constraintSetIDs of type String - List of handles to the constraintSet elements
— Input: wireID of type String - Handle to a port wire element

#### F.7.67.49 getPortWireDirection

Description: Returns the direction defined on the given port wire element.

— Returns: direction of type String - The port direction
— Input: wireID of type String - Handle to a port wire element

#### F.7.67.50 getPortWireDriverIDs

Description: Returns the handles to all the drivers defined on the given port wire element.

— Returns: driverIDs of type String - List of handles to the driver elements
— Input: wireID of type String - Handle to a port wire element

#### F.7.67.51 getPortWireID

Description: Returns the handle to wire element defined on the given port element.

— Returns: wireID of type String - Handle to the wire element
— Input: portID of type String - Handle to a port element

#### F.7.67.52 getPortWireQualifierID

Description: Returns the handle to the qualifier defined on the given component port wire element.

— Returns: qualifierID of type String - Handle to the qualifier element
— Input: wireID of type String - Handle to port wire element

#### F.7.67.53 getPortWireTypeDefIDs

Description: Returns the handles to all the wireTypeDefs defined on the given port element.

— Returns: wireTypeDefIDs of type String - List of handles to wireTypeDef elements
— Input: wireID of type String - Handle to a port wire element

#### F.7.67.54 getProtocolPayloadID

Description: Returns the handle to the payload defined on the given transactional port protocol element.

— Returns: payloadID of type String - Handle to a payload element
— Input: protocolID of type String - Handle to a protocol element

#### F.7.67.55 getProtocolProtocolType

Description: Returns the protocolType defined on the given protocol element.

— Returns: protocolType of type String - The protocol type
— Input: protocolID of type String - Handle to protocol element

#### F.7.67.56 getProtocolProtocolTypeID

Description: Returns the handle to the protocolType defined on the given protocol element.

— Returns: protocolTypeID of type String - Handle of protocol type
— Input: protocolID of type String - Handle to protocol element

#### F.7.67.57 getQualifierIsAddress

Description: Returns the isAddress boolean value of the given port qualifier element.

— Returns: isAddress of type Boolean - True if the isAddress qualifier is defined
— Input: qualifierID of type String - Handle to a qualifier element

#### F.7.67.58 getQualifierIsClock

Description: Returns the isClock boolean value of the given port qualifier element.

— Returns: isClock of type Boolean - True if the isClock qualifier is defined
— Input: qualifierID of type String - Handle to a qualifier element

#### F.7.67.59 getQualifierIsClockEn

Description: Returns the isClockEn boolean value of the given port qualifier element.

— Returns: isClockEn of type Boolean - True if the isClockEn qualifier is defined
— Input: qualifierID of type String - Handle to a qualifier element

#### F.7.67.60 getQualifierIsClockEnID

Description: Returns the handle to the isClockEn element defined on the given port qualifier element.

— Returns: isClockEnID of type String - Handle to the isClockEn element
— Input: qualifierID of type String - Handle to a qualifier element

#### F.7.67.61 getQualifierIsData

Description: Returns the isData boolean value of the given port qualifier element.

— Returns: isData of type Boolean - True if the isData qualifier is defined
— Input: qualifierID of type String - Handle to a qualifier element

#### F.7.67.62 getQualifierIsFlowControl

Description: Returns the isFlowControl boolean value of the given port qualifier element.

— Returns: isFlowControl of type Boolean - True if the isFlowControl qualifier is defined
— Input: qualifierID of type String - Handle to a qualifier element

#### F.7.67.63 getQualifierIsFlowControlID

Description: Returns the handle to the isFlowControl element defined on the given port qualifier element.

— Returns: isFlowControlID of type String - Handle to the isFlowControl element
— Input: qualifierID of type String - Handle to a qualifier element

#### F.7.67.64 getQualifierIsInterrupt

Description: Returns the isInterrupt boolean value of the given port qualifier element.

— Returns: isInterrupt of type Boolean - True if the isInterrupt qualifier is defined
— Input: qualifierID of type String - Handle to a qualifier element

#### F.7.67.65 getQualifierIsOpcode

Description: Returns the isOpCode boolean value of the given port qualifier element.

— Returns: isOpCode of type Boolean - True if the isOpCode qualifier is defined
— Input: qualifierID of type String - Handle to a qualifier element

#### F.7.67.66 getQualifierIsPowerEn

Description: Returns the isPowerEn boolean value of the given port qualifier element.

— Returns: isPowerEn of type Boolean - True if the isPowerEn qualifier is defined
— Input: qualifierID of type String - Handle to a qualifier element

#### F.7.67.67 getQualifierIsPowerEnID

Description: Returns the handle to the isPowerEn element defined on the given port qualifier element.

— Returns: isPowerEnID of type String - Handle to the isPowerEn element
— Input: qualifierID of type String - Handle to a qualifier element

#### F.7.67.68 getQualifierIsPowerEnPowerDomainRefByName

Description: Returns the powerDomain referenced from the given isPowerEn element.

— Returns: powerDomainRef of type String - The referenced powerDomain
— Input: powerEnID of type String - Handle to a powerEn element

#### F.7.67.69 getQualifierIsProtection

Description: Returns the isProtection boolean value of the given port qualifier element.

— Returns: isProtection of type Boolean - True if the isProtection qualifier is defined
— Input: qualifierID of type String - Handle to a qualifier element

#### F.7.67.70 getQualifierIsRequest

Description: Returns the isRequest boolean value of the given port qualifier element.

— Returns: isRequest of type Boolean - True if the isRequest qualifier is defined
— Input: qualifierID of type String - Handle to a qualifier element

#### F.7.67.71 getQualifierIsReset

Description: Returns the isReset boolean value of the given port qualifier element.

— Returns: isReset of type Boolean - True if the isReset qualifier is defined
— Input: qualifierID of type String - Handle to a qualifier element

#### F.7.67.72 getQualifierIsResetID

Description: Returns the handle to the isReset element defined on the given port qualifier element.

— Returns: isResetID of type String - Handle to the isReset element
— Input: qualifierID of type String - Handle to a qualifier element

#### F.7.67.73 getQualifierIsResponse

Description: Returns the isResponse boolean value of the given port qualifier element.

— Returns: isResponse of type Boolean - True if the isResponse qualifier is defined
— Input: qualifierID of type String - Handle to a qualifier element

#### F.7.67.74 getQualifierIsUser

Description: Returns the isUser boolean value of the given port qualifier element.

— Returns: isUser of type Boolean - True if the isUser qualifier is defined
— Input: qualifierID of type String - Handle to a qualifier element

#### F.7.67.75 getQualifierIsUserID

Description: Returns the handle to the isUser element defined on the given port qualifier element.

— Returns: isUserID of type String - Handle to the isUser element
— Input: qualifierID of type String - Handle to a qualifier element

#### F.7.67.76 getQualifierIsValid

Description: Returns the isValid boolean value of the given port qualifier element.

— Returns: isValid of type Boolean - True if the isValid qualifier is defined
— Input: qualifierID of type String - Handle to a qualifier element

#### F.7.67.77 getServiceTypeDefServiceTypeDefIDs

Description: Returns the handles to all the serviceTypeDefs defined on the given serviceTypeDef element.

— Returns: serviceTypeDefIDs of type String - List of handles to the serviceTypeDef elements
— Input: serviceTypeDefID of type String - Handle to a serviceTypeDef element

#### F.7.67.78 getServiceTypeDefTypeDefinitionIDs

Description: Returns the handles to all the typeDefinitions defined on the given serviceTypeDef element.

— Returns: typeDefinitionIDs of type String - List of handles to the typeDefinition elements
— Input: serviceTypeDefID of type String - Handle to a serviceTypeDef element

#### F.7.67.79 getServiceTypeDefTypeName

Description: Returns the typeName defined on the given serviceTypeDef element.

— Returns: typeName of type String - The service type
— Input: serviceTypeDefID of type String - Handle to a serviceTypeDef element

#### F.7.67.80 getServiceTypeDefTypeNameID

Description: Returns the handle to a typeName element.

— Returns: value of type String - The handle to a typeName element
— Input: serviceTypeDefID of type String - Handle to a serviceTypeDef element

#### F.7.67.81 getServiceTypeDefTypeParameterIDs

Description: Returns the handles to all the typeParameters defined on the given serviceTypeDef element.

— Returns: typeParameterIDs of type String - List of handles to the typeParameter elements
— Input: serviceTypeDefID of type String - Handle to a serviceTypeDef element

#### F.7.67.82 getServiceTypeDefTypeParametersIDs

Description: Returns the handles to all the typeParameters defined on the given serviceTypeDef element.

— Returns: typeParameterIDs of type String - List of handles to the typeParameter elements
— Input: serviceTypeDefID of type String - Handles to a serviceTypeDef element

#### F.7.67.83 getSignalTypeDefSignalType

Description: Returns the signalType defined on the given signalTypeDef element.

— Returns: signalType of type String - The signalType value. Can be one of the following:

continuous-conservative, continuous-non-conservative, discrete or digital.
— Input: signalTypeDefID of type String - Handle to a signalTypeDef

#### F.7.67.84 getSignalTypeDefViewIDs

Description: Returns the handles to all the views defined on the given typeDef element.

— Returns: viewIDs of type String - List of handles to the view elements
— Input: signalTypeDefID of type String - Handle to a signalTypeDef element

#### F.7.67.85 getSignalTypeDefViewRefIDs

Description: Returns the handles to all the viewRefs defined on the given TypeDef element.

— Returns: viewRefIDs of type String - List of handles to the viewRef elements
— Input: signalTypeDefID of type String - Handle to a signalTypeDef element

#### F.7.67.86 getSignalTypeDefViewRefs

Description: Returns all the viewRefs defined on the given signalTypeDef element.

— Returns: viewRefs of type String - List of the referenced views
— Input: signalTypeDefID of type String - Handle to a signalTypeDef element

#### F.7.67.87 getStrucPortTypeDefViewRefIDs

Description: Returns the handles to all the viewRefs defined on the given structPortTypeDef element.

— Returns: viewRefIDs of type String - List of handles to viewRef elements
— Input: structPortTypeDefID of type String - Handle to a structPortTypeDef element

#### F.7.67.88 getStructPortTypeDefRole

Description: Returns the role defined on the given structPortTypeDef element.

— Returns: role of type String - The structPort role
— Input: structPortTypeDefID of type String - Handle to a structPortTypeDef element

#### F.7.67.89 getStructPortTypeDefTypeDefinitionIDs

Description: Returns the handles to all the typeDefinitions defined on the given structPortTypeDef element.

— Returns: typeDefinitionIDs of type String - List of handles to the typeDefinition elements
— Input: structPortTypeDefID of type String - Handle to a structPortTypeDef element

#### F.7.67.90 getStructPortTypeDefTypeDefinitions

Description: Returns the typeDefinitions defined on the given structPortTypeDef element.

— Returns: typeDefinitions of type String - List of typeDefinitions
— Input: structPortTypeDefID of type String - Handle to a structPortTypeDef element

#### F.7.67.91 getStructPortTypeDefTypeName

Description: Returns the typeName defined on the given structPortTypeDef element.

— Returns: typeName of type String - The type name
— Input: structPortTypeDefID of type String - Handle to a structPortTypeDef element

#### F.7.67.92 getStructPortTypeDefTypeNameID

Description: Returns the handle to the typeName defined on the given structPortTypeDef element.

— Returns: typeNameID of type String - Handle to the typeName element
— Input: structPortTypeDefID of type String - Handle to a structPortTypeDef

#### F.7.67.93 getStructPortTypeDefTypeParameterIDs

Description: Returns the handles to all the typeParameters defined on the given structPortTypeDef element.

— Returns: typeParameterIDs of type String - List of handles to the typeParameter elements
— Input: structPortTypeDefID of type String - Handle to a structPortTypeDef element

#### F.7.67.94 getStructPortTypeDefViewIDs

Description: Returns the handles to all the views defined on the given structPortTypeDef element.

— Returns: viewIDs of type String - List of handles to the view elements
— Input: structPortTypeDefID of type String - Handle to a structPortTypeDef element

#### F.7.67.95 getSubPortPartSelectID

Description: Returns the handles to all the partSelect defined on the given subPort element.

— Returns: partSelectID of type String - Handle to the partSelect element defined on the subPort element

— Input: subPortID of type String - Handle to a subPort

#### F.7.67.96 getSubPortReferencePartSelectID

Description: Returns the handle to the partSelect defined on the given subPortReference element.

— Returns: partSelectID of type String - Handle to the partSelect element
— Input: subPortReferenceID of type String - Handle to a subPortReference element

#### F.7.67.97 getSubPortReferenceSubPortRefByName

Description: Returns the subPortRef defined on the given subPortReference element.

— Returns: subPortRef of type String - The referenced subPort name
— Input: subPortReferenceID of type String - Handle to a subPortReference element

#### F.7.67.98 getTransTypeDefServiceTypeDefIDs

Description: Returns the handles to all the serviceTypeDefs defined on the given transTypeDef element.

— Returns: serviceTypeDefIDs of type String - List of handles to the serviceTypeDef elements
— Input: transTypeDefID of type String - Handle to a transTypeDef

#### F.7.67.99 getTransTypeDefTypeDefinitionIDs

Description: Returns the handles to all the typeDefinitions defined on the given transTypeDef element.

— Returns: typeDefinitionIDs of type String - List of handles to the typeDefinition elements
— Input: transTypeDefID of type String - Handle to a transTypeDef element

#### F.7.67.100 getTransTypeDefTypeDefinitions

Description: Returns the typeDefinitions defined on the given transTypeDef element.

— Returns: typeDefinitions of type String - List of typeDefinitions
— Input: transTypeDefID of type String - Handle to a transTypeDef element

#### F.7.67.101 getTransTypeDefTypeName

Description: Returns the typeName defined on the given transTypeDef element.

— Returns: typeName of type String - The type name
— Input: transTypeDefID of type String - Handle to a transTypeDef element

#### F.7.67.102 getTransTypeDefTypeNameID

Description: Returns the handle to the typeName defined on the given transTypeDef element.

— Returns: typeNameID of type String - Handle to the typeName element
— Input: transTypeDefID of type String - Handle to a transTypeDef element

#### F.7.67.103 getTransTypeDefTypeParameterIDs

Description: Returns the handles to all the typeParameters defined on the given transTypeDef element.

— Returns: typeParameterIDs of type String - List of handles to the typeParameter elements
— Input: transTypeDefID of type String - Handle to a transTypeDef

#### F.7.67.104 getTransTypeDefTypeParametersIDs

Description: Returns the handles to all the typeParameters defined on the given transTypeDef element.

— Returns: typeParameterIDs of type String - List of handles to the typeParameter elements
— Input: transTypeDefID of type String - Handle to a transTypeDef element

#### F.7.67.105 getTransTypeDefViewRefByID

Description: Returns the view defined on the given viewRef element.

— Returns: viewID of type String - Handles to the referenced view element
— Input: transTypeDefID of type String - Handle to the transTypeDef element
— Input: viewRef of type String - Handle to the viewRef element

#### F.7.67.106 getTransTypeDefViewRefIDs

Description: Returns the handles to all the viewRefs defined on the given transTypeDef element.

— Returns: viewRefIDs of type String - List of handles to the viewRef elements
— Input: transTypeDefID of type String - Handle to a transTypeDef element

#### F.7.67.107 getWireTypeDefTypeDefinitionIDs

Description: Returns the handles to all the typeDefinitions defined on the given wireTypeDef element.

— Returns: typeDefinitionIDs of type String - List of handles to the typeDefinition elements
— Input: wireTypeDefID of type String - Handle to a wireTypeDef element

#### F.7.67.108 getWireTypeDefTypeDefinitions

Description: Returns the typeDefinitions defined on the given wireTypeDef element.

— Returns: typeDefinitions of type String - List of typeDefinitions
— Input: wireTypeDefID of type String - Handle to a wireTypeDef element

#### F.7.67.109 getWireTypeDefTypeName

Description: Returns the typeName defined on the given wireTypeDef element.

— Returns: typeName of type String - The type name
— Input: wireTypeDefID of type String - Handle to a wireTypeDef element

#### F.7.67.110 getWireTypeDefTypeNameID

Description: Returns the handle to the typeName defined on the given wireTypeDef element.

— Returns: typeNameID of type String - Handle to the typeName element
— Input: wireTypeDefID of type String - Handle to a wireTypeDef element

#### F.7.67.111 getWireTypeDefViewIDs

Description: Returns the handles to all the views defined on the given wireTypeDef element.

— Returns: viewIDs of type String - List of handles to the view elements
— Input: wireTypeDefID of type String - Handle to a wireTypeDef element

#### F.7.67.112 getWireTypeDefViewRefIDs

Description: Returns the handles to all the viewRefs defined on the given wireTypeDef element.

— Returns: viewRefIDs of type String - List of handles to the viewRef elements
— Input: wireTypeDefID of type String - Handle to a wireTypeDef element

#### F.7.67.113 getWireTypeDefViewRefs

Description: Returns all the viewRefs defined on the given wireTypeDef element.

— Returns: viewRefs of type String - List of the referenced views
— Input: wireTypeDefID of type String - Handle to a wireTypeDef element

### F.7.68 Port (EXTENDED)

#### F.7.68.1 addDomainTypeDefTypeDefinition

Description: Sets the typeDefinitions with the given definitions for the given domainTypeDef element.

— Returns: typeDefinitionID of type String - Handle of the new typeDefinition.
— Input: domainTypeDefID of type String - Handle to a domainTypeDef element
— Input: typeDefinition of type String - The type definition value

#### F.7.68.2 addDomainTypeDefViewRef

Description: Adds the given viewRef in the given domainTypeDef element.

— Returns: viewRefID of type String - Handle to the added viewRef
— Input: domainTypeDefID of type String - Handle to a domainTypeDef element
— Input: viewRef of type String - Name of the referenced view

#### F.7.68.3 addExternalPortReferenceSubPortReference

Description: Adds a reference to a subPort to the given externalPortReference of a structured port.

— Returns: subPortReferenceID of type String - The identifier of the added subPortReference
— Input: externalPortReferenceID of type String - Handle to an externalPortReference element

— Input: subPortRef of type String - Name of a subPort of the structured port

#### F.7.68.4 addFieldMapIndex

Description: Adds an index to the indices of the fieldMap element.

— Returns: indexID of type String - an identifier to the added index
— Input: fieldMapID of type String - Handle to a fieldMap element
— Input: value of type String - Index value expression

#### F.7.68.5 addFieldMapModeRef

Description: Adds a modeRef to a fieldMap element.

— Returns: modeRefID of type String - Handle to a modeRef element
— Input: fieldMapID of type String - Handle to a fieldMap element
— Input: modeRef of type String - the modeRef value to be added

#### F.7.68.6 addFieldMapSubPortReference

Description: Adds a subPortReference to a fieldMap element.

— Returns: subPortReferenceID of type String - the subPortReference identifier

— Input: fieldMapID of type String - Handle to a fieldMap element
— Input: subPortRef of type String - the subPort to be added

#### F.7.68.7 addInternalPortReferenceSubPortReference

Description: Adds a subPortReference to a subPort to the given internalPortReference of a structured port.

— Returns: subPortReferenceID of type String - The identifier of the added subPortReference
— Input: internalPortReferenceID of type String - Handle to an internalPortReference
— Input: subPortRef of type String - Name of a subPort of the structured port

#### F.7.68.8 addPortClockDriver

Description: Adds clockDriver with the given clock period, pulse offset, pulse value, and pulse duration to
the given port element.

— Returns: clockDriverID of type String - Handle to a new clockDriver
— Input: portID of type String - Handle to a port element
— Input: period of type Float - Clock period
— Input: offset of type Float - Clock pulse offset
— Input: value of type Long - Clock pulse value
— Input: duration of type Float - Clock pulse duration

#### F.7.68.9 addPortClockDriverExpresion

Description: Adds clockDriver with the given clock period, pulse offset, pulse value, and pulse duration to
the given port element.

— Returns: clockDriverID of type String - Handle to a new clockDriver
— Input: portID of type String - Handle to a port element
— Input: periodExpression of type String - Clock period
— Input: offsetExpression of type String - Clock pulse offset
— Input: valueExpression of type String - Clock pulse value
— Input: durationExpression of type String - Clock pulse duration

#### F.7.68.10 addPortDefaultDriver

Description: Adds defaultDriver with the given value to the given port element.

— Returns: driverID of type String - Handle to a new driver
— Input: portID of type String - Handle to a port element
— Input: value of type Long - Default driver value

#### F.7.68.11 addPortDefaultDriverExpression

Description: Adds defaultDriver with the given value to the given port element.

— Returns: driverID of type String - Handle to a new driver
— Input: portID of type String - Handle to a port element
— Input: valueExpression of type String - Default driver value

#### F.7.68.12 addPortDomainTypeDef

Description: Adds domainTypeDef for the given port wire element.

— Returns: domainTypeDefID of type String - Handle to the added domainTypeDef
— Input: wireID of type String - Handle to a port wire element

#### F.7.68.13 addPortFieldMap

Description: Adds a new fieldMap.

— Returns: portmapID of type String - Handle to the added fieldMap
— Input: portID of type String - Handle to a port element
— Input: memoryMapRef of type String - MemoryMap name (non null)
— Input: addressBlockRef of type String - AddressBlock name (non null)
— Input: registerRef of type String - Register name (non null)
— Input: fieldRef of type String - Field name (non null)

#### F.7.68.14 addPortSignalTypeDef

Description: Adds domainTypeDef for the given port wire element.

— Returns: signalTypeDefID of type String - Handle to the added signalTypeDef
— Input: wireID of type String - Handle to a port wire element
— Input: signalType of type String - The type of the signal. Can be one of

continuous-conservative or continuous-non-conservative or discrete or digital

#### F.7.68.15 addPortSingleShotDriver

Description: Adds singleShotDriver with the given offset, value, and duration to the given port element.

— Returns: singleShotDriverID of type String - Handle to a new singleShotDriver
— Input: portID of type String - Handle to a port element
— Input: offset of type Float - SingleShot offset
— Input: value of type Long - SingleShot value
— Input: duration of type Float - SingleShot duration

#### F.7.68.16 addPortSingleShotDriverExpression

Description: Adds singleShotDriver with the given offset, value, and duration to the given port element.

— Returns: singleShotDriverID of type String - Handle to a new singleShotDriver
— Input: portID of type String - Handle to a port element
— Input: offsetExpression of type String - The singleShot offset
— Input: valueExpression of type String - The singleShot value
— Input: durationExpression of type String - The singleShot duration

#### F.7.68.17 addPortStructuredStructPortTypeDef

Description: Adds a structPortTypeDef to the containing element.

— Returns: structPortTypeDefID of type String - Handle to the added structPortTypeDef
— Input: structuredID of type String - Handle to a port structured element
— Input: typeName of type String - Structured port definition type name

#### F.7.68.18 addPortStructuredSubStructuredPort

Description: Adds a subPort with structured to a port element.

— Returns: subPortID of type String - the ID of the created subPort
— Input: portID of type String - Handle to a port
— Input: subPortName of type String - name on the subPort
— Input: vectorLeft of type String - The vector left expression
— Input: vectorRight of type String - The vector right expression
— Input: subSubPortName of type String - The name of the subPort inside the subPort
— Input: structPortTypeDefTypeName of type String - The typeName of the

structPortTypeDef

#### F.7.68.19 addPortStructuredSubWirePort

Description: Adds a subPort with wire to a port structured element.

— Returns: subPortID of type String - The ID of the created subPort
— Input: structuredID of type String - Handle to structured
— Input: subPortName of type String - The name on the subPort
— Input: direction of type String - The port direction

#### F.7.68.20 addPortStructuredVector

Description: Adds a vector from a structured port.

— Returns: vectorID of type String - The vector identifier
— Input: structuredID of type String - Handle to a port structured element
— Input: left of type String - The left value
— Input: right of type String - The right value

#### F.7.68.21 addPortTransactionalTransTypeDef

Description: Adds transTypeDef for the given port element.

— Returns: transTypeDefID of type String - Handle to a new transTypeDef
— Input: transactionalID of type String - Handle to a port transactional element

#### F.7.68.22 addPortWireConstraintSet

Description: Adds constraintSet to the given wire element of a port.

— Returns: constraintSetID of type String - Handle to a new constraintSet
— Input: wireID of type String - Handle to a wire element

#### F.7.68.23 addPortWireDriver

Description: Adds driver without a value to the given port element.

— Returns: driverID of type String - Handle to a new driver
— Input: portWireID of type String - Handle to a port wire element
— Input: defaultValue of type String - The defaultValue expression

#### F.7.68.24 addPortWireTypeDef

Description: Adds wireTypeDef for the given port element.

— Returns: wireTypeDefID of type String - Handle to a new wireTypeDef
— Input: wireID of type String - Handle to a port wire

#### F.7.68.25 addServiceTypeDefServiceTypeDef

Description: Adds a serviceTypeDef to an existing serviceTypeDef on his typeParameters.

— Returns: serviceTypeDefID of type String - Handle to the added serviceTypeDef
— Input: serviceTypeDefID of type String - Handle to a serviceTypeDef element
— Input: typeName of type String - Service type name

#### F.7.68.26 addServiceTypeDefTypeDefinition

Description: Adds a TypeDefinition to the containing element.

— Returns: typeDefinitionID of type String - Handle to the added typeDefinition
— Input: serviceTypeDefID of type String - Handle to a serviceTypeDef element
— Input: typeDefinition of type String - Name of the file where the type is defined

#### F.7.68.27 addServiceTypeDefTypeParameter

Description: Adds a TypeParameter to the containing element.

— Returns: typeParameterID of type String - Handle to the added typeParameter
— Input: serviceTypeDefID of type String - Handle to a serviceTypeDef element
— Input: name of type String - Name of the parameter
— Input: value of type String - Value of the parameter

#### F.7.68.28 addSignalTypeDefViewRef

Description: Adds the given viewRef in the given signalTypeDef element.

— Returns: viewRefID of type String - Handle to the added viewRef
— Input: signalTypeDefID of type String - Handle to a signalTypeDef element
— Input: viewRef of type String - Name of the referenced view

#### F.7.68.29 addStructPortTypeDefTypeDefinition

Description: Adds typeDefinition to the containing element.

— Returns: typeDefinitionID of type String - Handle to the added typeDefinition
— Input: structPortTypeDefID of type String - Handle to a structPortTypeDef element
— Input: value of type String - File name containing the definition of the structured port type

#### F.7.68.30 addStructPortTypeDefTypeParameter

Description: Adds typeParameter to the containing element.

— Returns: typeParameterID of type String - Handle to the added typeParameter
— Input: structPortTypeDefID of type String - Handle to a strucPortTypeDef
— Input: name of type String - Parameter name

— Input: value of type String - Parameter value

#### F.7.68.31 addStructPortTypeDefViewRef

Description: Adds the given viewRef in the given structPortTypeDef element.

— Returns: viewRefID of type String - Handle to the added viewRef
— Input: structPortTypeDefID of type String - Handle to a structPortTypeDef element
— Input: viewRef of type String - Name of the referenced view

#### F.7.68.32 addTransTypeDefServiceTypeDef

Description: Adds a serviceTypeDef to the containing element.

— Returns: serviceTypeDefID of type String - Handle to the added serviceTypeDef
— Input: transTypeDefID of type String - Handle to a transTypeDef element
— Input: typeName of type String - Type name

#### F.7.68.33 addTransTypeDefTypeDefinition

Description: Adds a typeDefinition to the given transactional port type definition.

— Returns: typeDefinitionID of type String - The identifier of the added typeDefinition
— Input: transTypeDefID of type String - Handle to transTypeDef element
— Input: value of type String - Value of the added typeDefinition

#### F.7.68.34 addTransTypeDefTypeParameter

Description: Adds a typeParameter to the containing element.

— Returns: typeParameterID of type String - Handle to the added typeParameter
— Input: transTypeDefID of type String - Handle to a transTypeDef element
— Input: name of type String - Parameter name
— Input: value of type String - Parameter value

#### F.7.68.35 addTransTypeDefViewRef

Description: Adds the given viewRef in the given transTypeDef element.

— Returns: viewRefID of type String - Handle to the added viewRef
— Input: transTypeDefID of type String - Handle to a transTypeDef element
— Input: viewRef of type String - Name of the referenced view

#### F.7.68.36 addWireTypeDefTypeDefinition

Description: Adds the typeDefinition with the given definition for the given wireTypeDef element.

— Returns: typeDefinitionID of type String - The typeDefinition identifier
— Input: wireTypeDefID of type String - Handle to a wireTypeDef element
— Input: typeDefinition of type String - The Type definition to add

#### F.7.68.37 addWireTypeDefViewRef

Description: Adds the given viewRef in the given wireTypeDef element.

— Returns: viewRefID of type String - Handle to the added viewRef

— Input: wireTypeDefID of type String - Handle to a wireTypeDef element
— Input: viewRef of type String - Name of the referenced view

#### F.7.68.38 removeAbstractionDefPortPacket

Description: Removes the given packet from its containing logical port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: packetID of type String - Handle to a portPacketType element

#### F.7.68.39 removeAccessPortAccessType

Description: Removes portAccessType from the given access element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: accessID of type String - Handle to an access element

#### F.7.68.40 removeAllLogicalDirectionsAllowedAttribute

Description: Removes allLogicalDirectionsAllowed from the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: wireID of type String - Handle to a wire element

#### F.7.68.41 removeAllLogicalInitiativesAllowedAttribute

Description: Removes allLogicalInitiativesAllowed from the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: transactionalID of type String - Handle to a transactional element

#### F.7.68.42 removeDomainTypeDefTypeDefinition

Description: Removes the given typeDefinition from the domainTypeDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: typeDefinitionID of type String - Handle of type definition

#### F.7.68.43 removeDomainTypeDefTypeName

Description: Removes the typeName with the given value for the given domainTypeDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: domainTypeDefID of type String - Handle to a domainTypeDef element

#### F.7.68.44 removeDomainTypeDefViewRef

Description: Removes the given viewRef from its containing domainTypeDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: viewRefID of type String - Handle to a viewRef element

#### F.7.68.45 removeExactAttribute

Description: Removes the exact attribute of the transactional port type definition type name.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)

— Input: transTypeDefID of type String - Handle to a transTypeDef element

#### F.7.68.46 removeFieldMapModeRef

Description: Removes the given modeRef from its containing fieldMap element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: modeRefID of type String - the modeRef value to be removed

#### F.7.68.47 removeFieldMapPartSelect

Description: Removes a partSelect on the given fieldMap element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldMapID of type String - Handle to a portMap fieldMap element

#### F.7.68.48 removeFieldMapSubPortReference

Description: Removes the given subPortReference from its containing fieldMap element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: subPortRefID of type String - the subPort to be removed

#### F.7.68.49 removePayloadExtension

Description: Removes payload extension from the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: payloadID of type String - Handle to a protocol payload element

#### F.7.68.50 removePortAccess

Description: Removes port access from the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: portID of type String - Handle to a port element

#### F.7.68.51 removePortClockDriver

Description: Removes the given clockDriver element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: clockDriverID of type String - Handle to a clockDriver element

#### F.7.68.52 removePortDefaultDriver

Description: Removes the given defaultDriver element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: driverID of type String - Handle to a driver element

#### F.7.68.53 removePortDomainTypeDef

Description: Removes the given domainTypeDef from its containing port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: domainTypeDefID of type String - Handle to a domainTypeDef element

#### F.7.68.54 removePortFieldMap

Description: Removes the given fieldMap from its containing port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldMapID of type String - Handle to a fieldMap

#### F.7.68.55 removePortSignalTypeDef

Description: Removes the given signalTypeDef from its containing port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: signalTypeDefID of type String - Handle to a signalTypeDef element

#### F.7.68.56 removePortSingleShotDriver

Description: Removes the given singleShort driver element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: singleShotDriverID of type String - Handle to a singleShot driver element

#### F.7.68.57 removePortStructuredStructPortTypeDef

Description: Removes the given structPortTypeDef from its containing port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: structPortTypeDefID of type String - Handle to a strucPortTypeDef

#### F.7.68.58 removePortStructuredSubPort

Description: Removes the given subPort form its containing structured port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: subPortID of type String - Handle to a subPort element

#### F.7.68.59 removePortStructuredVector

Description: Removes the given vector from its containing structured port.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: vectorID of type String - Handle to a vector element

#### F.7.68.60 removePortTransactionalBusWidth

Description: Removes busWidth from the given port transactional element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: transactionalID of type String - Handle to a port transactional element

#### F.7.68.61 removePortTransactionalKind

Description: Removes kind from the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: transactionalID of type String - Handle to a port transactional element

#### F.7.68.62 removePortTransactionalMaxConnections

Description: Removes maxConnections from the given port transactional element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: transactionalID of type String - Handle to a port transactional element

#### F.7.68.63 removePortTransactionalMinConnections

Description: Sets minConnections from the given port transactional element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: transactionalID of type String - Handle to a port transactional element

#### F.7.68.64 removePortTransactionalPowerConstraint

Description: Removes the given power constraint from its containing transactional port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: powerConstraintID of type String - Handle to a power constraint

#### F.7.68.65 removePortTransactionalProtocol

Description: Removes protocol from transactional element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: transactionalID of type String - Handle to the identifier of a port transactional

#### F.7.68.66 removePortTransactionalQualifier

Description: Removes the given qualifier from its contained component port.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - Handle to qualifier

#### F.7.68.67 removePortTransactionalTransTypeDef

Description: Removes the given transTypeDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: transTypeDefID of type String - Handle to a transTypeDef element

#### F.7.68.68 removePortWireConstraintSet

Description: Removes the given constraintSet element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: constraintSetID of type String - Handle to a constraintSet element

#### F.7.68.69 removePortWireDriver

Description: Removes driver with the given driverID on wire port element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: driverID of type String - Handle to a driver element

#### F.7.68.70 removePortWirePowerConstraint

Description: Removes the given power constraint from its containing wire port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: powerConstraintID of type String - Handle to a power constraint

#### F.7.68.71 removePortWireQualifier

Description: Removes the given qualifier from its contained component port.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - Handle to qualifier

#### F.7.68.72 removePortWireTypeDef

Description: Removes the given wireTypeDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: wireTypeDefID of type String - Handle to a wireTypeDef element

#### F.7.68.73 removeProtocolPayload

Description: Removes custom attribute of protocolType from the given abstractionDefPort element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: protocolID of type String - Handle to protocol element

#### F.7.68.74 removeQualifierIsAddress

Description: Removes the isAddress qualifier for the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - the qualifier identifier

#### F.7.68.75 removeQualifierIsClock

Description: Removes the isClock qualifier for the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - the qualifier identifier

#### F.7.68.76 removeQualifierIsClockEn

Description: Removes the isClockEn qualifier for the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - the qualifier identifier

#### F.7.68.77 removeQualifierIsData

Description: Removes the isData qualifier for the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - the qualifier identifier

#### F.7.68.78 removeQualifierIsFlowControl

Description: Removes the isFlowControl qualifier for the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - the qualifier identifier

#### F.7.68.79 removeQualifierIsInterrupt

Description: Removes the isInterrupt qualifier for the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - the qualifier identifier

#### F.7.68.80 removeQualifierIsOpcode

Description: Removes the isOpCode qualifier for the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - the qualifier identifier

#### F.7.68.81 removeQualifierIsPowerEn

Description: Removes the isPowerEn qualifier for the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - the qualifier identifier

#### F.7.68.82 removeQualifierIsProtection

Description: Removes the isProtection qualifier for the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - the qualifier identifier

#### F.7.68.83 removeQualifierIsRequest

Description: Removes the isRequest qualifier for the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - the qualifier identifier

#### F.7.68.84 removeQualifierIsReset

Description: Removes the isReset qualifier for the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - the qualifier identifier

#### F.7.68.85 removeQualifierIsResponse

Description: Removes the isResponse qualifier for the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - the qualifier identifier

#### F.7.68.86 removeQualifierIsUser

Description: Removes the isUser qualifier of for the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - the qualifier identifier

#### F.7.68.87 removeQualifierIsValid

Description: Removes the isValid qualifier for the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - the qualifier identifier

#### F.7.68.88 removeServiceTypeDefServiceTypeDef

Description: Removes the given serviceTypeDef from its containing transactional port serviceTypeDef
element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: serviceTypeDefID of type String - Handle to a serviceTypeDef element

#### F.7.68.89 removeServiceTypeDefTypeDefinition

Description: Removes the given typeDefinition from its containing transactional port serviceTypeDef
element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: typeDefinitionID of type String - Handle to a typeDefinition

#### F.7.68.90 removeServiceTypeDefTypeParameter

Description: Removes the given typeParameter from its containing transactional port serviceTypeDef
element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: typeParameterID of type String - Handle to a typeParameter

#### F.7.68.91 removeSignalTypeDefViewRef

Description: Removes the given viewRef from its containing signalTypeDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: viewRefID of type String - Handle to a viewRef element

#### F.7.68.92 removeStructPortTypeDefRole

Description: Removes the role associated with the given structured port typeDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: structPortTypeDefID of type String - Handle to a structPortTypeDef element

#### F.7.68.93 removeStructPortTypeDefTypeDefinition

Description: Removes the given typeDefinition from its containing strucPortTypeDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: typeDefinitionID of type String - Handle to a typeDefinition element

#### F.7.68.94 removeStructPortTypeDefTypeParameter

Description: Removes the given typeParameter from its containing strucPortTypeDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: typeParameterID of type String - Handle to a typeParameter element

#### F.7.68.95 removeStructPortTypeDefViewRef

Description: Removes the given viewRef from its containing structPortTypeDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: viewRefID of type String - Handle to a viewRef element

#### F.7.68.96 removeSubPortMapPartSelect

Description: Removes a Part Select on a subPortMap element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: subPortMapID of type String - Handle to subPortMap element

#### F.7.68.97 removeSubPortReferencePartSelect

Description: Removes a partSelect on the given subPortReference element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: subPortReferenceID of type String - Handle to a portMap subPortReference element

#### F.7.68.98 removeTransTypeDefServiceTypeDef

Description: Removes the given serviceTypeDef from its containing transactional port type definition
element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: serviceTypeDefID of type String - Handle to a serviceTypeDef

#### F.7.68.99 removeTransTypeDefTypeDefinition

Description: Removes the given typeDefinition from its containing the transactional port type definition
element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: typeDefinitionID of type String - Handle to a typeDefinition element

#### F.7.68.100 removeTransTypeDefTypeName

Description: Removes the name of the transactional port type definition.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: transTypeDefID of type String - Handle to a transTypeDef element

#### F.7.68.101 removeTransTypeDefTypeParameter

Description: Removes the given typeParameter from its containing transactional port type definition
element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: typeParameterID of type String - Handle to a typeParameter

#### F.7.68.102 removeTransTypeDefViewRef

Description: Removes the given viewRef from its containing transTypeDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: viewRefID of type String - Handle to a viewRef element

#### F.7.68.103 removeWireTypeDefTypeDefinition

Description: Removes the typeDefinition from the wireTypeDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: typeDefinitionID of type String - Handle to type definition to remove

#### F.7.68.104 removeWireTypeDefTypeName

Description: Removes the typeName with the given value for the given wireTypeDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: wireTypeDefID of type String - Handle to a wireTypeDef element

#### F.7.68.105 removeWireTypeDefViewRef

Description: Removes the given viewRef from its containing wireTypeDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: viewRefID of type String - Handle to a viewRef element

#### F.7.68.106 setAbstractionDefBusType

Description: Sets the busType vlnv for the given abstraction definition object.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionDefinitionID of type String - Handle to the abstractionDefinition
— Input: vlnv of type String[] - VLNV of the busDefinition

#### F.7.68.107 setAccessPortAccessType

Description: Sets portAccessType with the given value for the given access element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: accessID of type String - Handle to an access element
— Input: accessType of type String - Port portAccessType

#### F.7.68.108 setExternalPortReferencePortReference

Description: Sets the portRef of the externalPort.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: externalPortReferenceID of type String - Handle to an externalPortReference element

— Input: value of type String - Name of the referenced port

#### F.7.68.109 setInternalPortReferenceComponentInstanceReference

Description: Sets the componentInstanceRef for the internal port reference.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: internalPortReferenceID of type String - Handle to an internalPortReference element

— Input: value of type String - Name of the referenced componentInstance

#### F.7.68.110 setInternalPortReferencePortReference

Description: Sets the portRef for the internal port reference.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: internalPortReferenceID of type String - Handle to an internalPortReference element

— Input: value of type String - Name of the referenced port

#### F.7.68.111 setDomainTypeDefTypeName

Description: Sets the typeName with the given value for the given domainTypeDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: domainTypeDefID of type String - Handle to a domainTypeDef element
— Input: typeName of type String - Value of the typeName element

#### F.7.68.112 setFieldMapAddressBlockRef

Description: Sets the addressBlockRef of the given fieldMap element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldMapID of type String - Handle to a fieldMap element
— Input: value of type String - AddressBlock name

#### F.7.68.113 setFieldMapFieldRef

Description: Sets the fieldRef of the given fieldMap element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldMapID of type String - Handle to a fieldMap element
— Input: value of type String - Field name

#### F.7.68.114 setFieldMapFieldSlice

Description: Sets the fieldSlice references on the given fieldMap element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldMapID of type String - Handle to a fieldMap element on a port
— Input: memoryMapRef of type String - Name of the referenced memoryMap
— Input: addressBlockRef of type String - Name of the referenced addressBlock
— Input: registerRef of type String - Name of the referenced register
— Input: fieldRef of type String - Name of the referenced field

#### F.7.68.115 setFieldMapMemoryMapRef

Description: Sets the memoryMapRef of the given fieldMap element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)

— Input: fieldMapID of type String - Handle to a fieldMap element
— Input: value of type String - MemoryMap name

#### F.7.68.116 setFieldMapPartSelect

Description: Sets a partSelect on the given fieldMap element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldMapID of type String - Handle to a portMap fieldMap element
— Input: range of type String[] - Create the range on the partSelect with “left” for range[0] and

“right” for range[1]. Set to null if you only want indices.

— Input: indices of type String[] - Handle to values of type String. Set all the index on the

partSelect

#### F.7.68.117 setFieldMapRegisterRef

Description: Sets the registerRef of the given fieldMap element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldMapID of type String - Handle to a fieldMap element
— Input: value of type String - Register name

#### F.7.68.118 setPayloadExtension

Description: Sets the name of the extension for the given payload.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: payloadID of type String - Handle to a payload element
— Input: extension of type String - Name of the extension

#### F.7.68.119 setPayloadType

Description: Sets the type on a payload element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: payloadID of type String - Handle to a payload element
— Input: type of type String - The payload type to set

#### F.7.68.120 setPortAccess

Description: Sets port access with the given value for the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: portID of type String - Handle to a port element

#### F.7.68.121 setPortStructured

Description: Sets the structured element in the given port.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: portID of type String - Handle to the identifier of a port element
— Input: subPortName of type String - The name of the subPort
— Input: structPortTypeDefTypeName of type String - The typeName of the

structPortTypeDef

#### F.7.68.122 setPortStructuredInterface

Description: Sets the interface on the given structured element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: structuredID of type String - Handle to a port structured
— Input: interfaceValue of type Boolean - The interface to set

#### F.7.68.123 setPortStructuredStruct

Description: Sets the struct element on the given structured element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: structuredID of type String - Handle to a port structured
— Input: direction of type String - The Struct direction to set

#### F.7.68.124 setPortStructuredUnion

Description: Sets the union element on the given structured element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: structuredID of type String - Handle to a port structured
— Input: direction of type String - The Union direction to set

#### F.7.68.125 setPortTransactional

Description: Sets the transactional element in the given port.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: portID of type String - Handle to the identifier of a port element
— Input: initiative of type String - The direction of the wire port. Can be one of the following:

requires, provides, both, or phantom

#### F.7.68.126 setPortTransactionalBusWidth

Description: Sets busWidth with the given value for the given port transactional element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: transactionalID of type String - Handle to a port transactional element
— Input: widthExpression of type String - Port busWidth

#### F.7.68.127 setPortTransactionalInitiative

Description: Sets initiative with the given value for the given port transactional element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: transactionalID of type String - Handle to a port transactional element
— Input: initiative of type String - Transactional port initiative

#### F.7.68.128 setPortTransactionalKind

Description: Sets kind with the given value for the given port transactional element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: transactionalID of type String - Handle to a port transactional element

— Input: kind of type String - Port kind

#### F.7.68.129 setPortTransactionalMaxConnections

Description: Sets maxConnections with the given value for the given port transactional element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: transactionalID of type String - Handle to a port transactional element
— Input: value of type String - Port maxConnections

#### F.7.68.130 setPortTransactionalMinConnections

Description: Sets minConnections with the given value for the given port transactional element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: transactionalID of type String - Handle to a port transactional element
— Input: value of type String - Port minConnections

#### F.7.68.131 setPortTransactionalProtocol

Description: Sets the protocol element on transactional element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: transactionalID of type String - Handle to the identifier of a port transactional
— Input: type of type String - protocol type. Can be one of the following: tlm or custom

#### F.7.68.132 setPortTransactionalQualifier

Description: Sets the qualifier on the given component port.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: transactionalID of type String - Handle to port transactional

#### F.7.68.133 setPortWire

Description: Sets the wire element on the given port.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: portID of type String - Handle to the identifier of a port element
— Input: direction of type String - The direction of the wire port. Can be one of the following: in,

out, inout, or phantom

#### F.7.68.134 setPortWireDirection

Description: Sets direction with the given value for the given port wire element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: wireID of type String - Handle to a port wire element
— Input: direction of type String - Port direction

#### F.7.68.135 setPortWireQualifier

Description: Sets the qualifier on the given component port.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: wireID of type String - Handle to port wire

#### F.7.68.136 setProtocolPayload

Description: Sets protocolType from the given protocol element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: protocolID of type String - Handle to protocol element
— Input: type of type String - type value. Can be one of the following: generic or specific

#### F.7.68.137 setProtocolProtocolType

Description: Sets custom attribute of protocolType from the given protocol element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: protocolID of type String - Handle to protocol element
— Input: protocolType of type String - protocol type value. Can be one of the following: tlm or

custom

#### F.7.68.138 setQualifierIsAddress

Description: Sets the isAddress qualifier for the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - the qualifier identifier
— Input: value of type Boolean - True if the port is an address (null to unset)

#### F.7.68.139 setQualifierIsClock

Description: Sets the isClock qualifier for the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - the qualifier identifier
— Input: value of type Boolean - True if the port is a clock (null to unset)

#### F.7.68.140 setQualifierIsClockEn

Description: Sets the isClockEn qualifier for the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - the qualifier identifier
— Input: value of type Boolean - True if the port is a clock enable (null to unset)

#### F.7.68.141 setQualifierIsData

Description: Sets the isData qualifier for the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - the qualifier identifier
— Input: value of type Boolean - True if the port is a data (null to unset)

#### F.7.68.142 setQualifierIsFlowControl

Description: Sets the isFlowControl qualifier for the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - the qualifier identifier

— Input: value of type Boolean - True if the port is a flow control (null to unset)

#### F.7.68.143 setQualifierIsInterrupt

Description: Sets the isInterrupt qualifier for the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - the qualifier identifier
— Input: value of type Boolean - True if the port is an interrupt (null to unset)

#### F.7.68.144 setQualifierIsOpcode

Description: Sets the isOpCode qualifier for the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - the qualifier identifier
— Input: value of type Boolean - True if the port is an opCode (null to unset)

#### F.7.68.145 setQualifierIsPowerEn

Description: Sets the isPowerEn qualifier for the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - The qualifier identifier
— Input: value of type Boolean - True if the port is a power enable (null to unset)

#### F.7.68.146 setQualifierIsProtection

Description: Sets the isProtection qualifier for the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - The qualifier identifier
— Input: value of type Boolean - True if the port is a protection (null to unset)

#### F.7.68.147 setQualifierIsRequest

Description: Sets the isRequest qualifier for the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - The qualifier identifier
— Input: value of type Boolean - True if the port is a request (null to unset)

#### F.7.68.148 setQualifierIsReset

Description: Sets the isReset qualifier for the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - The qualifier identifier
— Input: value of type Boolean - True if the port is a reset (null to unset)

#### F.7.68.149 setQualifierIsResponse

Description: Sets the isResponse qualifier for the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - The qualifier identifier

— Input: value of type Boolean - True if the port is a response (null to unset)

#### F.7.68.150 setQualifierIsUser

Description: Sets the isUser qualifier of for the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - The qualifier identifier
— Input: value of type Boolean - True if the port is an user defined qualifier (null to unset)

#### F.7.68.151 setQualifierIsValid

Description: Sets the isValid qualifier for the given port element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: qualifierID of type String - The qualifier identifier
— Input: value of type Boolean - True if the port is valid (null to unset)

#### F.7.68.152 setServiceTypeDefTypeName

Description: Sets the name of the transactional port service type definition.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: serviceTypeDefID of type String - Handle to a serviceTypeDef element
— Input: typeName of type String - Name ofthe service type

#### F.7.68.153 setSignalTypeDefSignalType

Description: Sets the signal type defined to the given signalTypeDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: signalTypeDefID of type String - Handle to the identifier of a signalTypeDef
— Input: signalType of type String - Name of the signalType. Can be one of the following:

continuous-conservative, continuous-non-conservative, or discrete or digital.

#### F.7.68.154 setStructPortTypeDefRole

Description: Sets the role associated with the given structured port typeDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: strucPortTypeDefID of type String - Handle to a structport typeDef element
— Input: role of type String - Role of this port

#### F.7.68.155 setStructPortTypeDefTypeName

Description: Sets the type name of the structured port.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: structPortTypeDefID of type String - Handle to a strucPortTypeDef
— Input: typename of type String - Type name

#### F.7.68.156 setSubPortReferencePartSelect

Description: Set a partSelect on the given subPortReference element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)

— Input: subPortReferenceID of type String - Handle to a portMap subPortReference element
— Input: range of type String[] - Create the range on the partSelect with “left” for range[0] and

“right” for range[1]. Set to null if you only want indices.

— Input: indices of type String[] - Handle to values of type String. Set all the index on the

partSelect

#### F.7.68.157 setTransTypeDefTypeName

Description: Sets the name of the transactional port type definition.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: transTypeDefID of type String - Handle to a transTypeDef element
— Input: typeName of type String - Port type name. For example, in SystemC, it could be: sc_port, or

sc_export, or my_tlm_port.

#### F.7.68.158 setWireTypeDefTypeName

Description: Sets the typeName with the given value for the given wireTypeDef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: wireTypeDefID of type String - Handle to a wireTypeDef element
— Input: typeName of type String - Value of the typeName element

### F.7.69 Port map (BASE)

#### F.7.69.1 getLogicalPortRange

Description: Returns the range left and right (resolved) value from the given logicalPort element.

— Returns: rangeValues of type Long - Array of two range values: left and right
— Input: logicalPortID of type String - Handle to a logicalPort element

#### F.7.69.2 getLogicalPortRangeExpression

Description: Returns the range left and right expressions defined on the given logicalPort element.

— Returns: rangeExpressions of type String - Array of two range expressions: left and right
— Input: logicalPortID of type String - Handle to a logicalPort element

#### F.7.69.3 getLogicalPortRangeLeftID

Description: Returns the handle to the left element defined on a logicalPort element.

— Returns: leftID of type String - Handle to the left element of the range
— Input: logicalPortID of type String - Handle to a logicalPort element

#### F.7.69.4 getLogicalPortRangeRightID

Description: Returns the handle to the right element defined on a logicalPort element.

— Returns: rightID of type String - Handle to the right element of the range
— Input: logicalPortID of type String - Handle to a logicalPort element

#### F.7.69.5 getPhysicalPortPartSelectID

Description: Returns the handle to the partSelect defined on the given physicalPort element.

— Returns: partSelectID of type String - Handle to the partSelect element
— Input: physicalPortID of type String - Handle to a physicalPort element

#### F.7.69.6 getPhysicalPortSubPortIDs

Description: Returns the handles to all the subPort defined on the given physicalPort element.

— Returns: subPortIDs of type String - List of handles to the subPort elements
— Input: physicalPortID of type String - Handle to a physicalPort element

#### F.7.69.7 getPortMapIsInformative

Description: Returns the isInformative defined on the given portMap element.

— Returns: value of type Boolean - True if portmap should be nestlisted, false otherwise
— Input: portMapID of type String - Handle to a portMap element

#### F.7.69.8 getPortMapLogicalPortID

Description: Returns the handle to the logicalPort defined on the given portMap element.

— Returns: logicalPortID of type String - Handle to the logicalPort
— Input: portMapID of type String - Handle to a portMap element

#### F.7.69.9 getPortMapLogicalTieOff

Description: Returns the logicalTieOff defined on the given portMap element.

— Returns: value of type Long - The logical port tieOff value
— Input: portMapID of type String - Handle to a portMap element

#### F.7.69.10 getPortMapLogicalTieOffExpression

Description: Returns the logicalTieOff expression defined on the given portMap element.

— Returns: expression of type String - The logical port tieOff expression
— Input: portMapID of type String - Handle to a portMap element

#### F.7.69.11 getPortMapLogicalTieOffID

Description: Returns the handle to the LogicalTieOff defined on the given portMap element.

— Returns: logicalTieOffID of type String - Handle to the LogicalTieOff element
— Input: portMapID of type String - Handle to a portMap element

#### F.7.69.12 getPortMapPhysicalPortID

Description: Returns the handle to the physicalPort defined on the given portMap element.

— Returns: physicalPortID of type String - Handle to the physicalPort
— Input: portMapID of type String - Handle to a portMap element

### F.7.70 Port map (EXTENDED)

#### F.7.70.1 addPhysicalPortSubPort

Description: Adds a subPort to the given physicalPort element

— Returns: subPortID of type String - Handle to a subPort element
— Input: physicalPortID of type String - Handle to a physicalPort element
— Input: name of type String - The subPort name

#### F.7.70.2 addPortMapPhysicalPortSubPort

Description: Adds a subPort to the containing element.

— Returns: subPortID of type String - Handle to the added subPort
— Input: portMapID of type String - Handle to a portMap element
— Input: name of type String - Name of the subPort

#### F.7.70.3 removePhysicalPortPartSelect

Description: Removes a partSelect on the given portMap physicalPort element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: physicalPortID of type String - Handle to a portMap physicalPort element

#### F.7.70.4 removePhysicalPortSubPort

Description: Removes the given subPort element from a physicalPort

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: subPortID of type String - Handle to a subPort element

#### F.7.70.5 removePortMapIsInformative

Description: Removes the isInformative from the given portMap element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: portMapID of type String - Handle to a portMap element

#### F.7.70.6 setAbstractionTypeAbstractionRef

Description: Sets the abstraction reference on the given abstractionType element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: abstractionTypeID of type String - Handle to an abstractionType element
— Input: vlnv of type String[] - The abstractionType reference

#### F.7.70.7 setLogicalPortRange

Description: Sets the range for the given logicalPort element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: logicalPortID of type String - Handle to a logicalPort element
— Input: range of type String[] - leftExpression at range index 0 & rightExpression at range 1

#### F.7.70.8 setPhysicalPortPartSelect

Description: Sets a partSelect on the given portMap physicalPort element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: physicalPortID of type String - Handle to a portMap physicalPort element
— Input: range of type String[] - Handle to of type String set the minimum (range[0]) and the

maximum (range[1]), on the partSelect

— Input: indices of type String[] - Handle to values of type String. Set all the index on the

partSelect

#### F.7.70.9 setPortMapIsInformative

Description: Sets the isInformative for the given portMap element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: portMapID of type String - Handle to a portMap element
— Input: value of type Boolean - IsInformative value

#### F.7.70.10 setPortMapLogicalPort

Description: Sets the logicalPort on the given portMap element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: portMapID of type String - Handle to a portMap element
— Input: name of type String - The logicalPort name

#### F.7.70.11 setPortMapLogicalTieOff

Description: Sets the logicalTieOff with the given value for the given portMap element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: portMapID of type String - Handle to an portMap element
— Input: expression of type String - logicalTieOff value

#### F.7.70.12 setPortMapPhysicalPort

Description: Sets the physicalPort on the given portMap element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: portMapID of type String - Handle to a portMap element
— Input: name of type String - The physicalPort name

#### F.7.70.13 setSubPortMapPartSelect

Description:

— Returns: partSelectID of type String - Handle to a partSelect element
— Input: subPortID of type String - Handle to a subPort element
— Input: range of type String[] - Create the range on the partSelect with “left” for range[0] and

“right” for range[1]. Set to null if you only want indices.

— Input: indices of type String[] - Handle to values of type String. Set all the index on the

partSelect

### F.7.71 Power (BASE)

#### F.7.71.1 getPortTransactionalPowerConstraintIDs

Description: Returns the handle to the powerConstraint defined on the given port transactional element.

— Returns: powerConstraintIDs of type String - List of handles to the powerConstraint elements
— Input: transactionalID of type String - Handle to a port transactional element

#### F.7.71.2 getPortWirePowerConstraintIDs

Description: Returns the handle to the powerConstraint defined on the given port wire element.

— Returns: powerConstraintIDs of type String - List of handles to the powerConstraint elements
— Input: wireID of type String - Handle to a port wire element

#### F.7.71.3 getPowerConstraintPowerDomainRefByID

Description: Returns the handle to the powerDomain referenced from the given powerConstraint element.

— Returns: powerDomainID of type String - Handle of the referenced power domain
— Input: powerConstraintID of type String - Handle to a powerConstraint element

#### F.7.71.4 getPowerConstraintPowerDomainRefByName

Description: Returns the powerDomain referenced from the given powerConstraint element.

— Returns: powerDomainRef of type String - The referenced powerDomain
— Input: powerConstraintID of type String - Handle to a powerConstraint element

#### F.7.71.5 getPowerConstraintRange

Description: Returns the range of the given powerConstraint.

— Returns: values of type String - Array of two range values: left and right
— Input: powerConstraintID of type String - Handle to a powerConstraint element

#### F.7.71.6 getPowerConstraintRangeLeftID

Description: Returns the handle to the left range of the given powerConstraint.

— Returns: leftID of type String - Handle to the left range
— Input: powerConstraintID of type String - Handle to a powerConstraint element

#### F.7.71.7 getPowerConstraintRangeRightID

Description: Returns the handle to the right range of the given powerConstraint.

— Returns: rightID of type String - Handle to the right range
— Input: powerConstraintID of type String - Handle to a powerConstraint element

#### F.7.71.8 getPowerDomainAlwaysOn

Description: Returns the alwaysOn resolved value defined on the given powerDomain element.

— Returns: value of type Boolean - True is the powerDomain is always on
— Input: powerDomainID of type String - Handle to a powerDomain element

#### F.7.71.9 getPowerDomainAlwaysOnExpression

Description: Returns the alwaysOn expression defined on the given powerDomain element.

— Returns: expression of type String - The expression on the alwaysON element
— Input: powerDomainID of type String - Handle to a powerDomain element

#### F.7.71.10 getPowerDomainAlwaysOnID

Description: Returns the alwaysOn identifer defined on the given powerDomain element.

— Returns: alwaysOnID of type String - Handle to an alwaysOn element
— Input: powerDomainID of type String - Handle to a powerDomain element

#### F.7.71.11 getPowerDomainName

Description: Returns the name of the given PowerDomain element.

— Returns: name of type String - The powerDomain name
— Input: powerDomainID of type String - Handle to a powerDomain element

#### F.7.71.12 getPowerDomainSubDomainOf

Description: Returns the parent power domain defined on the given powerDomain element.

— Returns: subDomainOf of type String - The referenced parent powerDomain
— Input: powerDomainID of type String - Handle to a powerDomain element

#### F.7.71.13 getPowerDomainSubDomainOfRefByID

Description: Returns the handle to the parent powerDomain referenced from the given powerDomain
element.

— Returns: powerDomainID of type String - Handle to the referenced powerDomain element
— Input: powerDomainID of type String - Handle to a powerDomain element

### F.7.72 Power (EXTENDED)

#### F.7.72.1 addComponentInstancePowerDomainLink

Description: Adds a Power Domain Link to the containing element.

— Returns: powerDomainLinkID of type String - the powerDomainLink identifier
— Input: componentInstanceID of type String - Handle to a componentInstance
— Input: externalPowerDomainRef of type String - Handle to the reference of a powerDomain

on the top Component

— Input: internalPowerDomainRef of type String[] - Handle to the reference of a powerDomain

defined on an instance

#### F.7.72.2 addComponentPowerDomain

Description: Adds a powerDomain to the given component.

— Returns: powerDomainID of type String - the new ID of the created powerDomain
— Input: componentID of type String - Handle to an component
— Input: name of type String - Handle to the name of a component

#### F.7.72.3 addPortTransactionalPowerConstraint

Description: Adds a powerConstraint to a transactional Port.

— Returns: powerConstraintID of type String - Handle to the added powerConstraint
— Input: transactionalID of type String - Handle to transactional element
— Input: powerDomainRef of type String - Handle to the reference of a powerDomain on the

powerConstraint

#### F.7.72.4 addPortWirePowerConstraint

Description: Adds a powerConstraint to a wire Port.

— Returns: powerConstraintID of type String - Handle to the added powerConstraint
— Input: wireID of type String - Handle to wire element
— Input: powerDomainRef of type String - Handle to the reference of a powerDomain on the

powerConstraint

#### F.7.72.5 addPowerDomainLinkInternalPowerDomainReference

Description: Adds an internalPowerDomainReference on a powerDomainLink element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: powerDomainLinkID of type String - Handle to a powerDomainLink element
— Input: internalPowerDomainReference of type String - the internal power reference to be

added

#### F.7.72.6 removeComponentInstancePowerDomainLink

Description: Removes the given PowerDomainRef from its containing componentInstance element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: powerDomainRefID of type String - Handle to a powerDomainRef

#### F.7.72.7 removeComponentPowerDomain

Description: Removes the given powerDomain from its containing component object.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: powerDomainID of type String - Handle to a powerDomain

#### F.7.72.8 removePowerConstraintRange

Description: Removes the range for the given PowerConstraint.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: powerConstraintID of type String - Handle to a powerConstraint

#### F.7.72.9 removePowerDomainLinkInternalPowerDomainRef

Description: Removes an internalPowerReference on a powerDomainLink.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: powerDomainLinkID of type String - Handle to a powerDomainLink element
— Input: internalPowerDomainRef of type String - The internalPowerDomainRef to remove

#### F.7.72.10 removePowerDomainSubDomainOf

Description: Removes the alwaysOn boolean on a powerDomain element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: powerDomainID of type String - Handle to a powerDomain element

#### F.7.72.11 setPowerConstraintPowerDomainRef

Description: Sets the powerDomainRef of the given powerConstraint.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: powerConstraintID of type String - Handle to a powerConstraint element
— Input: powerDomainRef of type String - Name of the referenced powerDomain

#### F.7.72.12 setPowerConstraintRange

Description: Sets the range for the given powerConstraint.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: powerConstraintID of type String - Handle to a powerConstraint
— Input: range of type String[] - Range, defined as a pair of left and right value expressions

#### F.7.72.13 setPowerDomainAlwaysOn

Description: Sets the alwaysOn boolean on a powerDomain element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: powerDomainID of type String - Handle to a powerDomain element
— Input: alwaysOn of type String - the always on value to set

#### F.7.72.14 setPowerDomainSubDomainOf

Description: Sets the alwaysOn boolean on a powerDomain element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: powerDomainID of type String - Handle to a powerDomain element
— Input: subDomainOf of type String - the subDomainOf on value to set

### F.7.73 Register (BASE)

#### F.7.73.1 getAliasOfAlternateRegisterRefByName

Description: Returns the alternateRef defined on the given aliasOf element.

— Returns: alternateRegisterRef of type String - The referenced alternateRegister
— Input: aliasOfID of type String - Handle to an aliasOf element

#### F.7.73.2 getAliasOfAlternateRegisterRefID

Description: Returns the handle to the alternateRegisterRef defined on the given aliasOf element.

— Returns: alternateRegisterRefID of type String - Handle to the alternateRegisterRef element

— Input: aliasOfID of type String - Handle to an aliasOf element

#### F.7.73.3 getAliasOfFieldRefByName

Description: Returns the fieldRef defined on the given aliasOf element.

— Returns: fieldRef of type String - The referenced register field
— Input: aliasOfID of type String - Handle to an aliasOf element

#### F.7.73.4 getAliasOfFieldRefID

Description: Returns the handle to the fieldRef defined on the given aliasOf element.

— Returns: fieldRefID of type String - Handle to the fieldRef element
— Input: aliasOfID of type String - Handle to an aliasOf element

#### F.7.73.5 getAliasOfRegisterRefByName

Description: Returns the registerRef defined on the given aliasOf element.

— Returns: registerRef of type String - The referenced register
— Input: aliasOfID of type String - Handle to an aliasOf element

#### F.7.73.6 getAliasOfRegisterRefID

Description: Returns the handle to the registerRef defined on the given aliasOf element.

— Returns: registerRefID of type String - Handle to the registerRef element
— Input: aliasOfID of type String - Handle to an aliasOf element

#### F.7.73.7 getAlternateRegisterFieldIDs

Description: Returns the handles to all the fields defined on the given alternateRegister element.

— Returns: regFieldIDs of type String - List of handles to the register field elements
— Input: alternateRegisterID of type String - Handle to an alternateRegister element

#### F.7.73.8 getAlternateRegisterModeRefIDs

Description: Returns the handles to all the modeRefs defined on the given alternateRegister.

— Returns: modeRefIDs of type String - List of handles to the modeRef elements
— Input: alternateRegisterID of type String - Handle to an alternateRegister element

#### F.7.73.9 getAlternateRegisterRefAlternateRegisterRefByName

Description: Returns the alternateRegisterRef defined on the given alternateRegisterRef element.

— Returns: alternateRegisterRef of type String - The referenced alternateRegister
— Input: alternateRegisterRefID of type String - Handle to an alternateRegisterRef element

#### F.7.73.10 getAlternateRegisterTypeIdentifier

Description: Returns the typeIdentifier defined on the given alternateRegister element.

— Returns: typeIdentifier of type String - The typeIdentifier value
— Input: alternateRegisterID of type String - Handle to an alternateRegister element

#### F.7.73.11 getAlternateRegisterVolatility

Description: Returns the volatile value defined on the given alternateRegister element.

— Returns: volatile of type Boolean - The volatile value
— Input: alternateRegisterID of type String - Handle to an alternateRegister element

#### F.7.73.12 getBroadcastToAddressBlockRefByName

Description: Returns the addressBlockRef defined on the given broadcastTo element.

— Returns: addressBlockRef of type String - The referenced addressBlock
— Input: broadcastToID of type String - Handle to a broadcastTo element

#### F.7.73.13 getBroadcastToAddressBlockRefID

Description: Returns the handle to the addressBlock defined on the given broadcastTo element.

— Returns: addressBlockID of type String - Handle to the addressBlock element
— Input: broadcastToID of type String - Handle to a broadcastTo element

#### F.7.73.14 getBroadcastToAddressSpaceRefByName

Description: Returns the addressSpaceRef defined on the given broadcastTo element.

— Returns: addressSpaceRef of type String - The referenced addressSpace
— Input: broadcastToID of type String - Handle to a broadcastTo element

#### F.7.73.15 getBroadcastToAddressSpaceRefID

Description: Returns the handle to the addressSpaceRef defined on the given broadcastTo element.

— Returns: addressSpaceRefID of type String - Handle to the addressSpaceRef element
— Input: broadcastToID of type String - Handle to a broadcastTo element

#### F.7.73.16 getBroadcastToAlternateRegisterRefByName

Description: Returns the alternateRegisterRef defined on the given broadcastTo element.

— Returns: alternateRegisterRef of type String - The referenced alternateRegister
— Input: broadcastToID of type String - Handle to a broadcastTo element

#### F.7.73.17 getBroadcastToAlternateRegisterRefID

Description: Returns the handle to the alternateRegisterRef defined on the given fieldSlice element.

— Returns: alternateRegisterRefID of type String - Handle to the alternateRegisterRef element

— Input: broadcastToID of type String - Handle to a broadcastTo element

#### F.7.73.18 getBroadcastToBankRefByNames

Description: Returns all the bankRefs defined on the given broadcastTo element.

— Returns: bankRef of type String - The list of all bankRef values
— Input: broadcastToID of type String - Handle to a broadcastTo element

#### F.7.73.19 getBroadcastToBankRefIDs

Description: Returns the handles to all the bankRefs defined on the given broadcastTo element.

— Returns: bankRefIDs of type String - List of handles to the bankRef elements
— Input: broadcastToID of type String - Handle to a broadcastTo element

#### F.7.73.20 getBroadcastToFieldRefByName

Description: Returns the fieldRef defined on the given broadcastTo element.

— Returns: fieldRef of type String - The referenced field
— Input: broadcastToID of type String - Handle to a broadcastTo element

#### F.7.73.21 getBroadcastToFieldRefID

Description: Returns the fieldRef defined on the given broadcastTo element.

— Returns: fieldRefID of type String - Handle to the fieldRef element
— Input: broadcastToID of type String - Handle to a broadcastTo element

#### F.7.73.22 getBroadcastToMemoryMapRefByName

Description: Returns the memoryMapRef defined on the given broadcastTo element.

— Returns: memoryMapRef of type String - The referenced memoryMap
— Input: broadcastToID of type String - Handle to a broadcastTo element

#### F.7.73.23 getBroadcastToMemoryMapRefID

Description: Returns the handle to the memoryMapRef defined on the given broadcastTo element.

— Returns: memoryMapRefID of type String - Handle to the memoryMapRef element
— Input: broadcastToID of type String - Handle to a broadcastTo element

#### F.7.73.24 getBroadcastToRegisterFileRefByNames

Description: Returns all the registerFileRefs defined on the given broadcastTo element.

— Returns: registerFileRefs of type String - List of the referenced registerFiles
— Input: broadcastToID of type String - Handle to a broadcastTo element

#### F.7.73.25 getBroadcastToRegisterFileRefIDs

Description: Returns all the registerFileRefs defined on the given broadcastTo element.

— Returns: registerFileRefIDs of type String - The list of all registerFileRef values
— Input: broadcastToID of type String - Handle to a broadcastTo element

#### F.7.73.26 getBroadcastToRegisterRefByName

Description: Returns the registerRef defined on the given broadcastTo element.

— Returns: registerRef of type String - The referenced register
— Input: broadcastToID of type String - Handle to a broadcastTo element

#### F.7.73.27 getBroadcastToRegisterRefID

Description: Returns the handle to the registerRef defined on the given broadcastTo element.

— Returns: registerRefID of type String - Handle to the RegisterRef element
— Input: broadcastToID of type String - Handle to a broadcastTo element

#### F.7.73.28 getEnumeratedValueExpression

Description: Returns the expression defined on the given enumerationValue element.

— Returns: expression of type String - The enumerationValue expression
— Input: enumeratedValueID of type String - Handle to an enumerationValue element

#### F.7.73.29 getEnumeratedValueUsage

Description: Returns the usage defined on the given enumeratedValue element.

— Returns: usage of type String - The usage
— Input: enumeratedValueID of type String - Handle to an enumeratedValue element

#### F.7.73.30 getEnumeratedValueValue

Description: Returns the value defined on the given enumeratedValue element.

— Returns: value of type Long - The enumeratedValue value
— Input: enumeratedValueID of type String - Handle to an enumeratedValue element

#### F.7.73.31 getEnumeratedValueValueExpression

Description: Returns the valueExpression defined on the given enumeratedValue element.

— Returns: valueExpression of type String - The enumerated value expression
— Input: enumeratedValueID of type String - Handle to an enumeratedValue element

#### F.7.73.32 getEnumeratedValueValueID

Description: Returns the handle to the value defined on the given enumeratedValue element.

— Returns: valueID of type String - Handle to the value element
— Input: enumeratedValueID of type String - Handle to an enumeratedValue element

#### F.7.73.33 getEnumeratedValuesEnumeratedValueIDs

Description: Returns the handles to all the enumeratedValues defined on the given enumeratedValues
element

— Returns: enumeratedValueIDs of type String - List of handles to the enumeratedValue elements

— Input: enumeratedValuesID of type String - Handle to an enumeratedValues element

#### F.7.73.34 getEnumeratedValuesEnumerationDefinitionRefByExternalTypeDefID

Description: Returns the handle to the externalTypeDefinitions referenced by the typeDefinitions attribute
of the enumerationDefinitionRef defined on the given enumeratedValues element.

— Returns: externalTypeDefID of type String - Handle to the externalTypeDefinitions element

referenced by the typeDefinitions attribute

— Input: enumeratedValuesID of type String - Handle to an enumeratedValues element

#### F.7.73.35 getEnumeratedValuesEnumerationDefinitionRefByID

Description: Returns the handle to the enumerationDefinition referenced from the given enumeratedValues
element

— Returns: enumerationDefinitionID of type String - Handle to the referenced

enumerationDefinition element

— Input: enumeratedValuesID of type String - Handle to an enumeratedValues element

#### F.7.73.36 getEnumeratedValuesEnumerationDefinitionRefByName

Description: Returns the enumerationDefinitionRefs defined on the given enumeratedValues element.

— Returns: enumerationDefinitionRef of type String - The referenced enumerationDefinition
— Input: enumeratedValuesID of type String - Handle to an enumeratedValues element

#### F.7.73.37 getEnumeratedValuesEnumerationDefinitionRefID

Description: Returns the handle to the enumerationDefinitionRef defined on the given enumeratedValues
element.

— Returns: enumerationDefinitionRefID of type String - Handle to the

enumerationDefinitionRef element

— Input: enumeratedValuesID of type String - Handle to an enumeratedValues element

#### F.7.73.38 getFieldBitOffsetID

Description: Returns the handle to the bitOffset defined on the given field element.

— Returns: bitOffsetID of type String - Handle to the bitOffset element
— Input: fieldID of type String - Handle to a field element

#### F.7.73.39 getFieldDefinitionBitWidthID

Description: Returns the handle to the bitWidth defined on the given fieldDefinition element.

— Returns: bitWidthID of type String - Handle to the bitWidth element
— Input: fieldDefinitionID of type String - Handle to a fieldDefinition element

#### F.7.73.40 getFieldDefinitionEnumeratedValueIDs

Description: Returns the handles to all the enumeratedValues defined on the given fieldDefinition element.

— Returns: enumeratedValueIDs of type String - List of handles to the enumeratedValue elements

— Input: fieldDefinitionID of type String - Handle to a fieldDefinition element

#### F.7.73.41 getFieldDefinitionTypeIdentifier

Description: Returns the typeIdentifier value of the given fieldDefinition element.

— Returns: typeIdentifier of type String - The value of the typeIdentifier defined on the

fieldDefinition

— Input: fieldDefinitionID of type String - Handle to a fieldDefinition element

#### F.7.73.42 getFieldDefinitionVolatile

Description: Returns the volatile Boolean of the given fieldDefinition.

— Returns: volatile of type Boolean - True if the field is volatile
— Input: fieldDefinitionID of type String - Handle to a fieldDefinition element

#### F.7.73.43 getFieldRefFieldRefByName

Description: Returns the fieldRef defined on the given fieldRef element.

— Returns: fieldRef of type String - The referenced field
— Input: fieldRefID of type String - Handle to a fieldRef element

#### F.7.73.44 getFieldRefIndexIDs

Description: Returns the handles to all the index elements defined on the given fieldRef element.

— Returns: indexIDs of type String - List of handles to the index elements
— Input: fieldRefID of type String - Handle to a fieldRef element

#### F.7.73.45 getRegisterAddressOffset

Description: Returns the addressOffset value defined on the given register element.

— Returns: addressOffset of type Long - The address offset
— Input: registerID of type String - Handle to a register element

#### F.7.73.46 getRegisterAddressOffsetExpression

Description: Returns the addressOffset expression defined on the given register element.

— Returns: addressOffsetExpression of type String - The addressOffset expression
— Input: registerID of type String - Handle to a register element

#### F.7.73.47 getRegisterAddressOffsetID

Description: Returns the handle to the AddressOffset defined on the given register element.

— Returns: addressOffsetID of type String - Handle to the addressOffset element
— Input: registerID of type String - Handle to a register element

#### F.7.73.48 getRegisterAlternateRegisterIDs

Description: Returns the handles to all the alternativeRegisters defined on the given register element.

— Returns: alternateRegisterIDs of type String - List of handles to the alternateRegister ele-

ments

— Input: registerID of type String - Handle to a register element

#### F.7.73.49 getRegisterFieldAliasOfID

Description: Returns the handle to the aliasOf defined on the given register field element.

— Returns: aliasOfID of type String - Handle to the aliasOf element
— Input: registerFieldID of type String - Handle to a register field element

#### F.7.73.50 getRegisterFieldBitOffset

Description: Returns the bitOffset in the given register field element.

— Returns: offset of type Long - Field bit offset
— Input: registerFieldID of type String - Handle to a register field element

#### F.7.73.51 getRegisterFieldBitOffsetExpression

Description: Returns the bitOffset expression in the given register field element.

— Returns: offsetExpression of type String - The bitOffset expression
— Input: registerFieldID of type String - Handle to a register field element

#### F.7.73.52 getRegisterFieldBitOffsetID

Description: Returns the handle to the bitOffset defined on the given register field element.

— Returns: bitOffsetID of type String - Handle to the bitOffset element
— Input: registerFieldID of type String - Handle to a register field element

#### F.7.73.53 getRegisterFieldBitWidth

Description: Returns the bitWidth element defined on the given register field element.

— Returns: width of type Long - The field width in bits
— Input: registerFieldID of type String - Handle to a register field element

#### F.7.73.54 getRegisterFieldBitWidthExpression

Description: Returns the bitWidth defined on the given register field element.

— Returns: width of type String - The bitWidth expression
— Input: registerFieldID of type String - Handle to a register field element

#### F.7.73.55 getRegisterFieldBitWidthID

Description: Returns the handle to the width defined on the given register field element.

— Returns: widthID of type String - Handle to the width element
— Input: registerFieldID of type String - Handle to a register field element

#### F.7.73.56 getRegisterFieldEnumeratedValuesID

Description: Returns the handle to the enumeratedValues defined on the given register field element.

— Returns: enumeratedValuesID of type String - Handle to the enumeratedValues element
— Input: registerFieldID of type String - Handle to a register field

#### F.7.73.57 getRegisterFieldFieldDefinitionRefByExternalTypeDefID

Description: Returns the handle to the externalTypeDefinitions referenced by the typeDefinitions attribute
of the fieldDefinitionRef defined on the given register field element.

— Returns: fieldDefinitionID of type String - Handle to the externalTypeDefinitions element

referenced by the typeDefinitions attribute

— Input: registerFieldID of type String - Handle to a register field element

#### F.7.73.58 getRegisterFieldFieldDefinitionRefByID

Description: Returns the handle to the fieldDefinition (defined in the typeDefinitions root object) referenced
from the given register field element.

— Returns: fieldDefinitionID of type String - Handle to the referenced fieldDefinition
— Input: registerFieldID of type String - Handle to a register field element

#### F.7.73.59 getRegisterFieldFieldDefinitionRefByName

Description: Returns the fieldDefinitionRef defined on the given register field element.

— Returns: fieldDefinitionRef of type String - The referenced fieldDefinition
— Input: registerFieldID of type String - Handle to a register field element

#### F.7.73.60 getRegisterFieldFieldDefinitionRefID

Description: Returns the handle to the fieldDefinitionRef element defined on the given register field
element.

— Returns: fieldDefinitionRefID of type String - Handle to the fieldDefinitionRef element
— Input: registerFieldID of type String - Handle to a register field element

#### F.7.73.61 getRegisterFieldIDs

Description: Returns the handles to all the fields defined on the given register element.

— Returns: regFieldIDs of type String - List of handles to the register field elements
— Input: registerID of type String - Handle to a register element

#### F.7.73.62 getRegisterFieldResetIDs

Description: Returns the handles to all the reset elements defined on the given register field element.

— Returns: resetIDs of type String - List of handles to the reset elements
— Input: registerFieldID of type String - Handle to a register field element

#### F.7.73.63 getRegisterFieldTypeIdentifier

Description: Returns the typeIdentifier element defined on the given register field element.

— Returns: typeIdentifier of type String - The type identifier
— Input: registerFieldID of type String - Handle to a register field element

#### F.7.73.64 getRegisterFieldVolatility

Description: Returns the volatile value defined on the given register field element.

— Returns: volatile of type Boolean - The volatile value
— Input: registerFieldID of type String - Handle to a register field element

#### F.7.73.65 getRegisterFileAddressOffsetID

Description: Returns the handle to the addressOffset defined on the given registerFile element.

— Returns: addressOffsetID of type String - Handle to the addressOffset element
— Input: registerFileID of type String - Handle to a registerFile element

#### F.7.73.66 getRegisterRefAttributeByID

Description: Returns the handle to register referenced from the given registerRef element.

— Returns: registerID of type String - Handle to the referenced register element
— Input: registerRefID of type String - Handle to the registerRef element

#### F.7.73.67 getRegisterRefIndexIDs

Description: Returns the handles to all the index elements defined on the given registerRef element.

— Returns: indexIDs of type String - List of handles to the index elements
— Input: registerRefID of type String - Handle to a registerRef element

#### F.7.73.68 getRegisterRefRegisterRefByName

Description: Returns the registerRef defined on the given registerRef element.

— Returns: registerRef of type String - The referenced register
— Input: registerRefID of type String - Handle to a registerRef element

#### F.7.73.69 getRegisterRegisterDefinitionRefByExternalTypeDefID

Description: Returns the handle to the externalTypeDefinitions referenced by the typeDefinitions attribute
of the registerDefinitionRef defined on the given register element.

— Returns: externalTypeDefinitionsID of type String - Handle to the
externalTypeDefinitions element referenced by the typeDefinitions attribute

— Input: registerID of type String - Handle to a register element

#### F.7.73.70 getRegisterRegisterDefinitionRefByID

Description: Returns the handle to the registerDefinition (defined in the typeDefinitions root object)
referenced from the given register element.

— Returns: registerDefinitionID of type String - Handle to the referenced registerDefinition
— Input: registerID of type String - Handle to a register element

#### F.7.73.71 getRegisterRegisterDefinitionRefByName

Description: Returns the registerDefinitionRef defined on the given register element.

— Returns: registerDefinitionRef of type String - The referenced registerDefinition
— Input: registerID of type String - Handle to a register element

#### F.7.73.72 getRegisterRegisterDefinitionRefID

Description: Returns the handle to the registerDefinitionRef element defined on the register element.

— Returns: registerDefinitionRefID of type String - Handle to the registerDefinitionRef element

— Input: registerID of type String - Handle to a register element

#### F.7.73.73 getRegisterSize

Description: Returns the size value defined on the given register element.

— Returns: size of type Long - The size value

— Input: registerID of type String - Handle to a register element

#### F.7.73.74 getRegisterSizeExpression

Description: Returns the size expression defined on the given register element.

— Returns: size of type String - The register size expression
— Input: registerID of type String - Handle to a register element

#### F.7.73.75 getRegisterSizeID

Description: Returns the handle to the size defined on the given register element.

— Returns: sizeID of type String - Handle to the size element
— Input: registerID of type String - Handle to a register element

#### F.7.73.76 getRegisterTypeIdentifier

Description: Returns the typeIdentifier defined on the given register element.

— Returns: typeIdentifier of type String - The typeIdentifier value
— Input: registerID of type String - Handle to a register element

#### F.7.73.77 getRegisterVolatility

Description: Returns the volatile value defined on the given register element.

— Returns: volatile of type Boolean - The volatile value
— Input: registerID of type String - Handle to a register element

#### F.7.73.78 getResetMask

Description: Returns the mask (resolved) value defined on the given reset element.

— Returns: mask of type Long - The mask value
— Input: resetID of type String - Handle to a reset element

#### F.7.73.79 getResetMaskExpression

Description: Returns the mask expression defined on the given reset element.

— Returns: expression of type String - The mask expression
— Input: resetID of type String - Handle to a reset element

#### F.7.73.80 getResetMaskID

Description: Returns the handle to the mask defined on the given reset element.

— Returns: maskID of type String - Handle to the mask element
— Input: resetID of type String - Handle to a reset element

#### F.7.73.81 getResetValue

Description: Returns the (resolved) value defined on the given reset element.

— Returns: value of type Long - The reset value
— Input: resetID of type String - Handle to a reset element

#### F.7.73.82 getResetValueExpression

Description: Returns the value expression defined on the given reset element.

— Returns: expression of type String - The value expression
— Input: resetID of type String - Handle to a reset element

#### F.7.73.83 getResetValueID

Description: Returns the handle to the value defined on the given reset element.

— Returns: valueID of type String - Handle to the reset value
— Input: resetID of type String - Handle to a reset element

### F.7.74 Register (EXTENDED)

#### F.7.74.1 addAlternateRegisterField

Description: Adds regField with the given name, offset, and width to the given alternateRegister element.

— Returns: regFieldID of type String - Handle to a new regField element
— Input: alternateRegisterID of type String - Handle to an alternateRegister element
— Input: name of type String - RegField name
— Input: offset of type String - RegField offset
— Input: width of type String - RegField width

#### F.7.74.2 addAlternaterRegisterModeRef

Description: Adds a modeRef to the given alternateRegister.

— Returns: modeRefID of type String - the modeRef identifier
— Input: alternateRegisterID of type String - Handle to an alternateRegister element
— Input: modeRef of type String - Name of the referenced mode
— Input: priority of type Long - The priority of the added mode reference

#### F.7.74.3 addBroadcastToBankRef

Description: Adds a bankRef on a broadcastTo element.

— Returns: bankRefID of type String - Handle to a bankRef identifier
— Input: broadcastToID of type String - Handle to an broadcast element
— Input: bankRef of type String - value of the bankRef to add

#### F.7.74.4 addBroadcastToRegisterFileRef

Description: Adds a registerRef on a broadcastTo element.

— Returns: registerFileRefID of type String - Handle to the added registerFileRef
— Input: broadcastToID of type String - Handle to a broadcastTo element
— Input: registerFileRef of type String - Name of the referenced registerFile

#### F.7.74.5 addEnumeratedValuesFieldEnumeratedValue

Description: Adds an enumeratedValue on the given enumeratedValues element

— Returns: enumeratedValueID of type String - Handle to a new enumeratedValue element
— Input: enumeratedValuesID of type String - Handle to an enumeratedValues element
— Input: name of type String - EnumeratedValue name
— Input: value of type String - EnumeratedValue value

#### F.7.74.6 addFieldRefIndex

Description: Adds an index to an fieldRef element.

— Returns: indexID of type String - Handle to the added index
— Input: fieldRefID of type String - Handle to a fieldRef element
— Input: value of type String - Index value

#### F.7.74.7 addRegisterAlternateRegister

Description: Adds an alternateRegister to the given register.

— Returns: alternateRegisterID of type String - Handle to the added alternateRegister
— Input: registerID of type String - Handle to a register element
— Input: name of type String - the name of the alternateRegister
— Input: modeRef of type String - the modeRef to set on the alternate register
— Input: priority of type Long - the priority of the modeRef
— Input: fieldName of type String - the field name on the alternateRegister
— Input: fieldOffset of type String - the Offset of the field on the alternateRegister
— Input: fieldWidth of type String - the width of the field on the alternateRegister

#### F.7.74.8 addRegisterField

Description: Adds regField with the given name, offset, and width to the given register element.

— Returns: regFieldID of type String - Handle to a new regField element
— Input: registerID of type String - Handle to a register element
— Input: name of type String - RegField name
— Input: offset of type String - RegField offset
— Input: width of type String - RegField width

#### F.7.74.9 addRegisterFieldReset

Description: Adds a reset with the given type and value to the given regField element.

— Returns: resetID of type String - Handle to the added reset
— Input: registerFieldID of type String - Handle to a regField element
— Input: value of type String - Reset value expression

#### F.7.74.10 addRegisterRefIndex

Description: Adds an index to a registerRef element.

— Returns: indexID of type String - Handle to the added index
— Input: registerRefID of type String - Handle to a registerRef element
— Input: value of type String - Index value

#### F.7.74.11 removeAliasOfAlternateRegisterRef

Description: Removes an alternateRegisterRef on an aliasOf element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: aliasOfID of type String - Handle of an aliasOf element

#### F.7.74.12 removeAliasOfRegisterRef

Description: Removes the registerRef on an aliasOf of a field element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: aliasOfID of type String - Handle to an aliasOf element

#### F.7.74.13 removeAlternateRegisterField

Description: Removes the given regField element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: regFieldID of type String - Handle to a regField element

#### F.7.74.14 removeAlternateRegisterTypeIdentifier

Description: Removes typeIdentifier from the given alternateRegister element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: alternateRegisterID of type String - Handle to an alternateRegister element

#### F.7.74.15 removeAlternateRegisterVolatility

Description: Removes volatility from the given alternateRegister element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: alternateRegisterID of type String - Handle to an alternateRegister element

#### F.7.74.16 removeAlternaterRegisterModeRef

Description: Removes the given modeRef from its containing element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: modeRefID of type String - Handle to a modeRef element

#### F.7.74.17 removeBroadcastToAddressBlockRef

Description: Removes the AddressBlock for a broadcastTo element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: broadcastToID of type String - Handle to a broadcastTo element

#### F.7.74.18 removeBroadcastToAlternateRegisterRef

Description: Removes an alternateRegisterRef on a broadcastTo element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: broadcastToID of type String - Handle of a broadcastTo element

#### F.7.74.19 removeBroadcastToBankRef

Description: Removes the given bankRef from its containing broadcastTo element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: bankRefID of type String - Handle a bankRef element

#### F.7.74.20 removeBroadcastToMemoryMapRef

Description: Removes the memoryMapRef for a broadcastTo element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: broadcastToID of type String - Handle to a broadcastTo element

#### F.7.74.21 removeBroadcastToRegisterFileRef

Description: Removes the given registerRef from its containing broadcastTo element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerRefID of type String - Handle to a registerRef element

#### F.7.74.22 removeBroadcastToRegisterRef

Description: Removes the RegisterRef for a broadcastTo element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: broadcastToID of type String - Handle to a broadcastTo element

#### F.7.74.23 removeEnumeratedValuesEnumeratedValue

Description: Removes the given enumeratedValue element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: enumeratedValueID of type String - Handle to an enumeratedValue element

#### F.7.74.24 removeFieldRefIndex

Description: Removes the given index from its containing fieldRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indexID of type String - Handle to an index element

#### F.7.74.25 removeRegisterAlternateRegister

Description: Removes the given alternateRegister element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: alternateRegisterID of type String - Handle to an alternateRegister element

#### F.7.74.26 removeRegisterField

Description: Removes the given register field element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerFieldID of type String - Handle to a field of a register element

#### F.7.74.27 removeRegisterFieldArray

Description: Removes the array element from the given register field.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerFieldID of type String - Handle to a registerField element

#### F.7.74.28 removeRegisterFieldBitWidth

Description: Removes the bitWidth element from the given register field.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerFieldID of type String - Handle to a registerField element

#### F.7.74.29 removeRegisterFieldEnumeratedValues

Description: Removes the enumeratedValues element from a field of a register

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerFieldID of type String - Handle to a register Field element

#### F.7.74.30 removeRegisterFieldFieldAccessPolicices

Description: Removes the fieldAccessPolicies on the given field on a register

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerFieldID of type String - Handle to an field on a register element

#### F.7.74.31 removeRegisterFieldReset

Description: Removes the given reset element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: resetID of type String - Handle to a reset element

#### F.7.74.32 removeRegisterFieldTypeIdentifier

Description: Removes the typeIdentifier from the given register field element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerFieldID of type String - Handle to a register field element

#### F.7.74.33 removeRegisterFieldVolatility

Description: Removes the volatility from the given register field element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerFieldID of type String - Handle to a register field element

#### F.7.74.34 removeRegisterRefIndex

Description: Removes the given index from its containing registerRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indexID of type String - Handle to an index element

#### F.7.74.35 removeRegisterTypeIdentifier

Description: Removes typeIdentifier from the given register element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerID of type String - Handle to a register element

#### F.7.74.36 removeRegisterVolatility

Description: Removes volatility from the given register element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerID of type String - Handle to a register element

#### F.7.74.37 removeResetMask

Description: Removes the mask from the given reset element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: resetID of type String - Handle to a reset element

#### F.7.74.38 removeUsageAttribute

Description: Removes the value of the usage field of an EnumeratedValue

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: enumeratedValueID of type String - Handle to an enumeratedValue element

#### F.7.74.39 setAliasOfAlternateRegisterRef

Description: Sets an alternateRegisterRef on an aliasOf element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: aliasOfID of type String - Handle of an aliasOf element
— Input: alternateRegisterRef of type String - the alternateRegisterRef value to set

#### F.7.74.40 setAliasOfFieldRef

Description: Sets the fieldRef on the aliasOf of a field element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: aliasOfID of type String - Handle to an alias element
— Input: fieldRef of type String - Name of the referenced field

#### F.7.74.41 setAliasOfRegisterRef

Description: Sets the registerRef on an aliasOf of a field element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: aliasOfID of type String - Handle to an aliasOf element
— Input: registerRef of type String - Name of the referenced register

#### F.7.74.42 setAlternateRegisterTypeIdentifier

Description: Sets typeIdentifier with the given value for the given alternateRegister element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)

— Input: alternateRegisterID of type String - Handle to an alternateRegister element
— Input: typeIdentifier of type String - The alternateRegister typeIdentifier

#### F.7.74.43 setAlternateRegisterVolatility

Description: Sets volatility with the given value for the given alternateRegister element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: alternateRegisterID of type String - Handle to an alternateRegister element
— Input: _volatile of type Boolean - The alternateRegister volatility

#### F.7.74.44 setBroadcastToAddressBlockRef

Description: Sets the addressBlock for a broadcastTo element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: broadcastToID of type String - Handle to a broadcastTo element
— Input: addressBlockRef of type String - Name of the referenced addressBlock

#### F.7.74.45 setBroadcastToAlternateRegisterRef

Description: Sets an alternateRegisterRef on a broadcastTo element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: broadcastToID of type String - Handle of a broadcastTo element
— Input: alternateRegisterRef of type String - the alternateRegisterRef value to set

#### F.7.74.46 setBroadcastToFieldRef

Description: Sets the fieldRef for a broadcastTo element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: broadcastToID of type String - Handle to a broadcastTo element
— Input: fieldRef of type String - Handle to a field to a register

#### F.7.74.47 setBroadcastToMemoryMapRef

Description: Sets the memoryMapRef for a broadcastTo element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: broadcastToID of type String - Handle to a broadcastTo element
— Input: memoryMapRef of type String - Name of the referenced memoryMap

#### F.7.74.48 setBroadcastToRegisterRef

Description: Sets the RegisterRef for a broadcastTo element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: broadcastToID of type String - Handle to a broadcastTo element
— Input: registerRef of type String - Name of the referenced register

#### F.7.74.49 setEnumeratedValueUsage

Description: Sets the value of the usage field of an enumeratedValue

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)

— Input: enumeratedValueID of type String - Handle to an enumeratedValue element
— Input: usage of type String - Usage enumerated value. Can be one of: read, write or read-write

#### F.7.74.50 setEnumeratedValueValue

Description: Sets the expression associated with the given EnumeratedValue.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: enumeratedValueID of type String - Handle to an enumeratedValue element
— Input: expression of type String - New expression

#### F.7.74.51 setEnumeratedValuesEnumerationDefinitionRef

Description: Sets the enumerationDefinitionRef on the given enumeratedValues element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: enumeratedValuesID of type String - Habndle to an enumeratedValues element
— Input: enumerationDefinitionRef of type String - The enumerationDefinition reference
— Input: typeDefinitions of type String - The referenced externalType definition

#### F.7.74.52 setFieldDefinitionBitWidth

Description: Sets the bitWidth expression of the given fieldDefinition.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldDefinitionID of type String - Handle to the fieldDefinition
— Input: value of type String - Handle to the new value

#### F.7.74.53 setFieldDefinitionTypeIdentifier

Description: Sets the typeIdentifier string of the given fieldDefinition.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldDefinitionID of type String - Handle to the fieldDefinition
— Input: value of type String - Handle to the new value

#### F.7.74.54 setFieldDefinitionVolatile

Description: Sets the volatile Boolean of the given fieldDefinition.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldDefinitionID of type String - the identifier of the fieldDefinition
— Input: value of type Boolean - Handle to the new value

#### F.7.74.55 setModeRefPriority

Description: Sets the priority on the given modeRef.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: modeRefID of type String - Handle to a modeRef element
— Input: priority of type Long - Priority value

#### F.7.74.56 setRegisterAddressOffset

Description: Sets the addressOffset for the given register element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerID of type String - Handle to a register element
— Input: value of type String - value to set on the addressOffset

#### F.7.74.57 setRegisterFieldAliasOf

Description: Sets an aliasOf element on a field of a register and returns his ID.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerFieldID of type String - Handle to an field on a register element
— Input: fieldRef of type String - Name of the referenced field

#### F.7.74.58 setRegisterFieldBitWidth

Description: Sets the bitWith on a field of a register element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerFieldID of type String - Handle to a register field element
— Input: value of type String - Handle value of the bitWidth

#### F.7.74.59 setRegisterFieldEnumeratedValues

Description: Sets the enumeratedValues element on the given field of register element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerFieldID of type String - Handle to the field on a register

#### F.7.74.60 setRegisterFieldFieldAccessPolicies

Description: Sets the fieldACcessPolicies on the given field on a register.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerFieldID of type String - Handle to an field on a register element

#### F.7.74.61 setRegisterFieldFieldDefinitionRef

Description: Sets the fieldDefinitionRef on the given field of a register.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerFieldID of type String - Handle to a field element on a register
— Input: value of type String - Handle to th fieldDefinitionRef value
— Input: typeDefinitions of type String - the typeDefinitions value

#### F.7.74.62 setRegisterFieldTypeIdentifier

Description: Sets the typeIdentifier with the given value to the given register field element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: regFieldID of type String - Handle to a register field element
— Input: typeIdentifier of type String - Register field typeIdentifier

#### F.7.74.63 setRegisterFieldVolatility

Description: Sets the volatile flag with the given value to the given register field element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)

— Input: regFieldID of type String - Handle to a register field element
— Input: volatile of type Boolean - Register field volatility

#### F.7.74.64 setRegisterRegisterDefinitionRef

Description: Sets the registerDefinitionRef on the register.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerID of type String - Handle to a register element
— Input: value of type String - Name of the referenced registerDefinition in an

externalTypeDefinitions

— Input: typeDefinitions of type String - Name of the component externalTypeDefinitions

#### F.7.74.65 setRegisterSize

Description: Sets the size for the given register element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerID of type String - Handle to a register element
— Input: value of type String - Value to set on the size

#### F.7.74.66 setRegisterTypeIdentifier

Description: Sets typeIdentifier with the given value for the given register element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerID of type String - Handle to a register element
— Input: typeIdentifier of type String - Register typeIdentifier

#### F.7.74.67 setRegisterVolatility

Description: Sets volatility with the given value for the given register element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerID of type String - Handle to a register element
— Input: volatile of type Boolean - Register volatility

#### F.7.74.68 setResetMask

Description: Sets the mask with the given value for the given reset element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: resetID of type String - Handle to a reset element
— Input: mask of type String - Reset mask expression

#### F.7.74.69 setResetValue

Description: Sets the value on a reset element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: resetID of type String - Handle to a reset element
— Input: value of type String - Value to set on the reset

### F.7.75 Register file (BASE)

#### F.7.75.1 getAliasOfRegisterFileRefByNames

Description: Returns all the registerFileRefs defined on the given aliasOf element.

— Returns: registerFileRef of type String - List of registerFileRef names
— Input: aliasOfID of type String - Handle to an aliasOf element

#### F.7.75.2 getAliasOfRegisterFileRefIDs

Description: Returns the handles to all the registerFileRefs defined on the given aliasOf element.

— Returns: registerFileRefIDs of type String - List of handles to the referenced registerFile elements

— Input: aliasOfID of type String - Handle to an aliasOf element

#### F.7.75.3 getRegisterFileAccessHandleIDs

Description: Returns the handles to all the accessHandles defined on the given registerFile element.

— Returns: accessHandleIDs of type String - List of handles to accessHandle elements
— Input: registerFileID of type String - Handle to a registerFile element

#### F.7.75.4 getRegisterFileAccessPolicyIDs

Description: Returns the handles to all the accessPolicies defined on the given registerFile element.

— Returns: accessPolicyIDs of type String - List of handles to the accessPolicy elements
— Input: registerFileID of type String - Handle to a registerFile element

#### F.7.75.5 getRegisterFileAddressOffset

Description: Returns the addressOffset in the given registerFile element.

— Returns: addressOffset of type Long - RegisterFile addressOffset
— Input: registerFileID of type String - Handle to a registerFile element

#### F.7.75.6 getRegisterFileAddressOffsetExpression

Description: Returns the addressOffset expression defined on the given registerFile element.

— Returns: addressOffset of type String - The addressOffset expression
— Input: registerFileID of type String - Handle to a registerFile element

#### F.7.75.7 getRegisterFileArrayID

Description: Returns the handle to the array defined on the given registerFile element.

— Returns: arrayID of type String - Handle to the registerFile array
— Input: registerFileID of type String - Handle to a registerFile element

#### F.7.75.8 getRegisterFileRange

Description: Returns the range defined on the given registerFile element.

— Returns: range of type Long - The range value (expressed as the number of addressable units)
— Input: registerFileID of type String - Handle to a registerFile element

#### F.7.75.9 getRegisterFileRangeExpression

Description: Returns the range expression defined on the given registerFile element.

— Returns: range of type String - The range expression
— Input: registerFileID of type String - Handle to a registerFile element

#### F.7.75.10 getRegisterFileRangeID

Description: Returns the handle to the range defined on the given registerFile element.

— Returns: rangeID of type String - Handle to the range
— Input: registerFileID of type String - Handle to a registerFile element

#### F.7.75.11 getRegisterFileRefIndexIDs

Description: Returns the handles to all the indices defined on the given addressBlockRef element.

— Returns: indicesIDs of type String - List of handles to the index elements
— Input: addressBlockRefID of type String - Handle to an addressBlockRef element

#### F.7.75.12 getRegisterFileRegisterFileDefinitionRefByExternalTypeDefID

Description: Returns the handle to the externalTypeDefinitions referenced by the typeDefinitions attribute
of the registerFileDefinitionRef defined on the given registerFile element.

— Returns: registerFileDefinitionID of type String - Handle to the externalTypeDefinitions element referenced by the typeDefinitions attribute

— Input: registerFileID of type String - Handle to a registerFile element

#### F.7.75.13 getRegisterFileRegisterFileDefinitionRefByID

Description: Returns the handle to the registerFileDefinition referenced from the given registerFile element.

— Returns: registerFileDefinitionID of type String - Handle to the referenced

registerFileDefinition element

— Input: registerFileID of type String - Handle to a registerFile element

#### F.7.75.14 getRegisterFileRegisterFileDefinitionRefByName

Description: Returns the registerFileDefinitionRef value defined on the given registerFile element.

— Returns: registerFileDefinitionRef of type String - The registerFileDefinitionRef on a

registerFile element

— Input: registerFileID of type String - Handle to a registerFile element

#### F.7.75.15 getRegisterFileRegisterFileDefinitionRefID

Description: Returns the handle to the registerFileDefinitionRef defined on the given registerFile element.

— Returns: registerFileDefinitionRefID of type String - Handle to the

registerFileDefinitionRef element

— Input: registerFileID of type String - Handle to the a registerFile element

#### F.7.75.16 getRegisterFileRegisterFileIDs

Description: Returns the handles to all the registerFiles defined on the given registerFile element.

— Returns: registerFileIDs of type String - List of handles to registerFile elements
— Input: registerFileID of type String - Handle to a registerFile element

#### F.7.75.17 getRegisterFileRegisterIDs

Description: Returns the handles to all the registers defined on the given registerFile element.

— Returns: registerIDs of type String - List of handles to the register elements
— Input: registerFileID of type String - Handle to a registerFile element

#### F.7.75.18 getRegisterFileTypeIdentifier

Description: Returns the typeIdentifier defined on the given registerFile element.

— Returns: typeIdentifier of type String - The typeIdentifier value
— Input: registerFileID of type String - Handle to a registerFile element

### F.7.76 Register file (EXTENDED)

#### F.7.76.1 addAliasOfRegisterFileRef

Description: Adds a registerFileRef on an aliasOf of a field of a register element.

— Returns: registerFileRefID of type String - the registerFileRef identifier on the aliasOf
— Input: aliasOfID of type String - Handle to an aliasOf element
— Input: registerFileRef of type String - Name of the referenced registerFile

#### F.7.76.2 addRegisterFileDefinitionRegisterFile

Description: Adds a registerFile to the given registerFileDefinition element.

— Returns: registerFileID of type String - Handle to the added registerFile
— Input: registerFileDefinitionID of type String - Handle to a registerFileDefinition
— Input: name of type String - Handle to the name of the registerFile to create
— Input: addressOffset of type String - Handle to a registerFile address offset
— Input: range of type String - Handle to a registerFile range

#### F.7.76.3 addRegisterFileRefIndex

Description: Adds an index to a registerFileRef element.

— Returns: indexID of type String - Handle to the added index
— Input: registerFileRefID of type String - Handle to a registerFileRef element
— Input: value of type String - Index value

#### F.7.76.4 addRegisterFileRegister

Description: Adds a register with the given name, offset, and size, and a field with the given name, offset,
and width to the given registerFile.

— Returns: registerID of type String - Handle to a new register element
— Input: registerFileID of type String - Handle to a registerFile element
— Input: name of type String - Register name
— Input: offset of type String - Register offset

— Input: size of type String - Register size
— Input: fieldName of type String - Field name
— Input: fieldOffset of type String - Field offset
— Input: fieldWidth of type String - Field width

#### F.7.76.5 removeAliasOfRegisterFileRef

Description: Removes the given registerFileRef from its containing aliasOf element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerFileRefID of type String - Handle to a registerFileRef element

#### F.7.76.6 removeRegisterFileAccessHandle

Description: Removes the given access handle from its containing register file element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: accessHandleID of type String - Handle to the accessHandle to remove

#### F.7.76.7 removeRegisterFileRefIndex

Description: Removes the given index from its containing registerFileRef element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: indexID of type String - Handle to an index element

#### F.7.76.8 removeRegisterFileRegister

Description: Removes the given register from its containing registerFile element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerID of type String - Handle to a register element

#### F.7.76.9 removeRegisterFileRegisterFile

Description: Removes the given RegisterFile from its containing registerFile element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerFileID of type String - Handle to the element to remove

#### F.7.76.10 removeRegisterFileTypeIdentifier

Description: Removes the typeIdentifier with the given value in the given registerFile element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerFileID of type String - Handle to a registerFile element

#### F.7.76.11 setRegisterFileAddressOffset

Description: Sets the value of the addressOffset expression of the given registerFile.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerFileID of type String - Handle to a registerFile
— Input: expression of type String - the new value for the expression

#### F.7.76.12 setRegisterFileRange

Description: sets the range expression of a registerFile of the given registerFile.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerFileID of type String - Handle to a registerFile
— Input: expression of type String - Handle to the new value for the expression

#### F.7.76.13 setRegisterFileRegisterFileDefinitionRef

Description: Sets the registerFileDefinitionRef on a registerFile element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerFileID of type String - Handle to a registerFile element
— Input: value of type String - Name of the referenced registerFileDefinition in an externalTypeDefinitions
— Input: typeDefinitions of type String - Name of the component externalTypeDefinitions

#### F.7.76.14 setRegisterFileTypeIdentifier

Description: Sets the typeIdentifier with the given value in the given registerFile element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerFileID of type String - Handle to a registerFile element
— Input: typeIdentifier of type String - RegisterFile typeidentifier

### F.7.77 Slice (BASE)

#### F.7.77.1 getFieldSliceAddressBlockRefByID

Description: Returns the addressBlockID referenced by the given fieldSlice element.

— Returns: addressBlockID of type String - Handle to the referenced addressBlock element
— Input: fieldSliceID of type String - Handle to a fieldSlice element

#### F.7.77.2 getFieldSliceAddressBlockRefByName

Description: Returns the addressBlockRef defined on the given fieldSlice element.

— Returns: addressBlockRef of type String - The referenced addressBlock
— Input: fieldSliceID of type String - Handle to a fieldSlice element

#### F.7.77.3 getFieldSliceAddressBlockRefID

Description: Returns the handle to the addressBlockRef defined on the given fieldSlice element.

— Returns: addressBlockRefID of type String - Handle to the addressBlockRef element
— Input: fieldSliceID of type String - Handle to a fieldSlice element

#### F.7.77.4 getFieldSliceAddressSpaceRefByID

Description: Returns the addressSpaceID from the given fieldSlice element.

— Returns: addressSpaceID of type String - Handle to a addressSpace element
— Input: fieldSliceID of type String - Handle to a fieldSlice element

#### F.7.77.5 getFieldSliceAddressSpaceRefByName

Description: Returns the addressSpaceRef defined on the given fieldSlice element.

— Returns: addressSpaceRef of type String - The referenced addressSpace
— Input: fieldSliceID of type String - Handle to a fieldSlice element

#### F.7.77.6 getFieldSliceAddressSpaceRefID

Description: Returns the handle to the addressSpaceRef defined on the given fieldSlice element.

— Returns: addressSpaceRefID of type String - Handle to the addressSpaceRef element
— Input: fieldSliceID of type String - Handle to a fieldSlice element

#### F.7.77.7 getFieldSliceAlternateRegisterRefByID

Description: Returns the alternateRegisterID from the given fieldSlice element.

— Returns: alternateRegisterID of type String - Handle to a alternateRegister element
— Input: fieldSliceID of type String - Handle to a fieldSlice element

#### F.7.77.8 getFieldSliceAlternateRegisterRefByName

Description: Returns the alternateRegisterRef defined on the given fieldSlice element.

— Returns: alternateRegisterRef of type String - The referenced alternateRegister name
— Input: fieldSliceID of type String - Handle to a fieldSlice element

#### F.7.77.9 getFieldSliceAlternateRegisterRefID

Description: Returns the handle to the alternateRegisterRef defined on the given fieldSlice element.

— Returns: alternateRegisterRefID of type String - Handle to the alternateRegisterRef element
— Input: fieldSliceID of type String - Handle to a fieldSlice element

#### F.7.77.10 getFieldSliceBankRefByNames

Description: Returns all the bankRefs defined on the given fieldSlice element.

— Returns: bankRefs of type String - List of the referenced banks
— Input: fieldSliceID of type String - Handle to a fieldSlice element

#### F.7.77.11 getFieldSliceBankRefIDs

Description: Returns the handles to all the bankRefs defined on the given fieldSlice element

— Returns: bankRefIDs of type String - List of handles to the bankRef elements
— Input: fieldSliceID of type String - Handle to a fieldSlice

#### F.7.77.12 getFieldSliceFieldRefByName

Description: Returns the FieldRef defined on the given fieldSlice element.

— Returns: FieldRef of type String - The referenced field element
— Input: fieldSliceID of type String - Handle to a fieldSlice

#### F.7.77.13 getFieldSliceFieldRefID

Description: Returns the handle to the fieldRef defined on the given fieldSlice element.

— Returns: FieldRefID of type String - Handle to the fieldRef element
— Input: fieldSliceID of type String - Handle to a fieldSlice element

#### F.7.77.14 getFieldSliceMemoryMapRefByID

Description: Returns the memoryMapID referenced by the given fieldSlice element.

— Returns: memoryMapID of type String - Handle to the referenced memoryMap element
— Input: fieldSliceID of type String - Handle to a fieldSlice element

#### F.7.77.15 getFieldSliceMemoryMapRefByName

Description: Returns the memoryMapRef defined on the given fieldSlice element.

— Returns: memoryMapRef of type String - The referenced memoryMap
— Input: fieldSliceID of type String - Handle to a fieldSlice element

#### F.7.77.16 getFieldSliceMemoryMapRefID

Description: Returns the handle to the memoryMapRef defined on the given fieldSlice element.

— Returns: memoryMapRefID of type String - Handle to the referenced memoryMap
— Input: fieldSliceID of type String - Handle to a fieldSlice element

#### F.7.77.17 getFieldSliceMemoryRemapRefByID

Description: Returns the memoryRemapID referenced by the given fieldSlice element.

— Returns: memoryRemapID of type String - Handle to the referenced memoryRemap element
— Input: fieldSliceID of type String - Handle to a fieldSlice element

#### F.7.77.18 getFieldSliceMemoryRemapRefByName

Description: Returns the memoryRemapRef defined on the given fieldSlice element.

— Returns: memoryRemapRef of type String - The memoryMap reference
— Input: fieldSliceID of type String - Handle to a fieldSlice element

#### F.7.77.19 getFieldSliceMemoryRemapRefID

Description: Returns the handle to the memoryRemapRef defined on the given fieldSlice element.

— Returns: memoryRemapRefID of type String - Handle to the memoryMap reference
— Input: fieldSliceID of type String - Handle to a fieldSlice element

#### F.7.77.20 getFieldSliceRange

Description: Returns the range defined on the given fieldSlice element.

— Returns: values of type String - Array of two range values: left and right
— Input: fieldSliceID of type String - Handle to a fieldSlice element

#### F.7.77.21 getFieldSliceRangeLeftID

Description: Returns the handle to the left range defined on the given fieldSlice element.

— Returns: leftID of type String - Handle to the left element
— Input: fieldSliceID of type String - Handle to a fieldSlice element

#### F.7.77.22 getFieldSliceRangeRightID

Description: Returns the handle to the right range defined on the given fieldSlice element.

— Returns: rightID of type String - Handle to the right element
— Input: fieldSliceID of type String - Handle to a fieldSlice element

#### F.7.77.23 getFieldSliceRegisterFileRefByNames

Description: Returns all the registerFileRefs defined on the given fieldSlice element.

— Returns: registerFileRef of type String - List of the referenced registerFiles
— Input: fieldSliceID of type String - Handle to a fieldSlice element

#### F.7.77.24 getFieldSliceRegisterFileRefIDs

Description: Returns the handles to all the registerFileRefs defined on the given fieldSlice element.

— Returns: registerFileID of type String - List of the registerFileRef elements
— Input: fieldSliceID of type String - Handle to a fieldSlice element

#### F.7.77.25 getFieldSliceRegisterRefByID

Description: Returns the registerID referenced by the given fieldSlice element.

— Returns: registerID of type String - Handle to the referenced register element
— Input: fieldSliceID of type String - Handle to a fieldSlice element

#### F.7.77.26 getFieldSliceRegisterRefByName

Description: Returns the registerRef defined on the given fieldSlice element.

— Returns: registerRef of type String - The referenced registerRef element
— Input: fieldSliceID of type String - Handle to a fieldSlice element

#### F.7.77.27 getFieldSliceRegisterRefID

Description: Returns the handle to the registerRef defined on the given fieldSlice element.

— Returns: registerRefID of type String - Handle to the registerRef element
— Input: fieldSliceID of type String - Handle to a fieldSlice element

#### F.7.77.28 getLocationSliceIDs

Description: Returns the handles to all the slices defined on the given location element.

— Returns: sliceIDs of type String - List of handles to the slice elements
— Input: locationID of type String - Handle to a location element

#### F.7.77.29 getModeFieldSliceIDs

Description: Returns all the handle to the fieldSlice defined on the given mode element.

— Returns: fieldSliceIDs of type String - List of handles to the fieldSlice elements
— Input: modeID of type String - Handle to a mode element

#### F.7.77.30 getModePortSliceIDs

Description: Returns the handles to all the slices defined on the given mode element.

— Returns: portSliceIDs of type String - List of handles to the portSlice elements
— Input: modeID of type String - Handle to a mode element

#### F.7.77.31 getPortSlicePartSelectID

Description: Returns the handle to the partSelect defined on the given portSlice element.

— Returns: partSelectID of type String - Handle to the partSelect element
— Input: portSliceID of type String - Handle to a portSlice element

#### F.7.77.32 getPortSlicePortRefByName

Description: Returns the portRef defined on the given portSlice element.

— Returns: portRef of type String - The referenced port
— Input: portSliceID of type String - Handle to a portSlice element

#### F.7.77.33 getPortSliceSubPortReferenceIDs

Description: Returns all the subPortRefs defined on a portSlice element.

— Returns: subPortRefs of type String - List of the referenced subPorts
— Input: portSliceID of type String - Handle to a portSlice element

#### F.7.77.34 getSlicePathSegmentIDs

Description: Returns the handles to all the pathSegments defined on the given slice element.

— Returns: pathSegmentIDs of type String - List of handles to pathSegment elements
— Input: sliceID of type String - Handle to a slice element

#### F.7.77.35 getSliceRange

Description: Returns the range defined on the given slice element.

— Returns: range of type Long - Array of two range values: left and right
— Input: sliceID of type String - Handle to a slice element

#### F.7.77.36 getSliceRangeExpression

Description: Returns the range left and right expressions defined on the given slice element.

— Returns: expressions of type String - Array of two range expressions: left and right
— Input: sliceID of type String - Handle to a slice element

#### F.7.77.37 getSliceRangeLeftID

Description: Returns the handle to the left range defined on the given slice element.

— Returns: leftRangeID of type String - Handle to the left range
— Input: sliceID of type String - Handle to a slice element

#### F.7.77.38 getSliceRangeRightID

Description: Returns the handle to the right range defined on the given slice element.

— Returns: rightRangeID of type String - Handle to the right range
— Input: sliceID of type String - Handle to a slice element

### F.7.78 Slice (EXTENDED)

#### F.7.78.1 addFieldSliceBankRef

Description: Adds bank reference to a fieldSlice element.

— Returns: bankRefID of type String - Handle to the new bankRef element
— Input: fieldSliceID of type String - Handle to a fieldSlice element
— Input: bankRef of type String - Name of the referenced bank

#### F.7.78.2 addFieldSliceRegisterFileRef

Description: Adds a registerFileRef on a fieldSlice element.

— Returns: registerFileRefID of type String - the registerFileRef identifier
— Input: fieldSliceID of type String - Handle to a fieldSlice element
— Input: registerFileRef of type String - Name of the referenced registerFile

#### F.7.78.3 addModeFieldSlice

Description: Adds an fieldSlice on mode element.

— Returns: fieldSliceID of type String - a fieldSlice identifier
— Input: modeID of type String - Handle to a mode element
— Input: name of type String - Name of a fieldSlice
— Input: memoryMapRef of type String - Name of the referenced memoryMap
— Input: addressBlockRef of type String - Name of the referenced addressBlock
— Input: registerRef of type String - Name of the referenced register
— Input: fieldRef of type String - Name of the referenced field

#### F.7.78.4 addModePortSlice

Description: Adds a portSlice on a Mode element.

— Returns: portSliceID of type String - Handle to the added portSlice
— Input: modeID of type String - Handle to a mode element
— Input: name of type String - Name of the port slice
— Input: portRef of type String - Name of the referenced port

#### F.7.78.5 addPortSliceSubPortReference

Description: Adds a subPortReference to an portSlice element.

— Returns: subPortReferenceID of type String - Handle to the added subPortReference
— Input: portSliceID of type String - Handle to a portSlice element
— Input: subPortRef of type String - Name of the referenced subPort

#### F.7.78.6 addSlicePathSegment

Description: Adds a pathSegment element to a given slice element.

— Returns: pathSegmentID of type String - Handle to the added pathSegment
— Input: sliceID of type String - Handle to a slice element
— Input: pathSegmentValue of type String - Handle to value of the pathSegment

#### F.7.78.7 removeFieldSliceAlternateRegisterRef

Description: Removes an alternateRegisterRef on a fieldSlice element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldSliceID of type String - Handle of a fieldSlice element

#### F.7.78.8 removeFieldSliceBankRef

Description: Removes the given bank reference from the given fieldSlice element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: bankRefID of type String - Handle to a bankRef element

#### F.7.78.9 removeFieldSliceMemoryRemapRef

Description: Removes the memoryRemap reference on an fieldSlice element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldSliceID of type String - Handle to an fieldSlice element

#### F.7.78.10 removeFieldSliceRange

Description: Removes a range on the given fieldSlice element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldSliceID of type String - Handle to a fieldSlice element

#### F.7.78.11 removeFieldSliceRegisterFileRef

Description: Removes the given registerFileRef from its containing fieldSlice element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldSliceID of type String - Handle to a fieldSlice element

#### F.7.78.12 removeLocationSlice

Description: Removes the given slice from its containing location element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: sliceID of type String - Handle to a slice element

#### F.7.78.13 removeModeFieldSlice

Description: Removes the given fieldSlice from its containing mode element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldSliceID of type String - Handle to a fieldSlice element

#### F.7.78.14 removeModePortSlice

Description: Removes the given portSlice from its containing mode element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: portSliceID of type String - Handle to a portSlice element

#### F.7.78.15 removePortSlicePartSelect

Description: Removes a partSelect on the given portSlice element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: portSliceID of type String - Handle to a portMap portSlice element

#### F.7.78.16 removePortSliceSubPortReference

Description: Removes the given subPortReference from its containing portSlice element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: subPortReferenceID of type String - Handle to a subPortRefrence element

#### F.7.78.17 removeSlicePathSegment

Description: Removes the given pathSegment element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: pathSegmentID of type String - Handle to a pathSegment element

#### F.7.78.18 removeSliceRange

Description: Removes the range from the given slice element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: sliceID of type String - Handle to a slice element

#### F.7.78.19 setFieldSliceAddressBlockRef

Description: Sets the addressBlockRef of a fieldSlice element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldSliceID of type String - Handle to a fieldSlice element
— Input: addressBlockRef of type String - Name of the referenced addressBlock

#### F.7.78.20 setFieldSliceAddressSpaceRef

Description: Sets the addressSpaceRef set on a fieldSlice element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldSliceID of type String - Handle to a fieldSlice element
— Input: addressSpaceRef of type String - set the addressSpaceRef on a fieldSlice element

#### F.7.78.21 setFieldSliceAlternateRegisterRef

Description: Sets an alternateRegisterRef on a fieldSlice element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldSliceID of type String - Handle of a fieldSlice element
— Input: alternateRegisterRef of type String - the alternateRegisterRef value to set

#### F.7.78.22 setFieldSliceFieldRef

Description: Sets the fieldRef on a fieldSlice element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldSliceID of type String - Handle to a fieldSlice element
— Input: fieldRef of type String - Name of the referenced field

#### F.7.78.23 setFieldSliceMemoryMapRef

Description: Sets the memoryMapRef on a fieldSlice element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldSliceID of type String - Handle to an fieldSlice element
— Input: memoryMapRef of type String - Name of the referenced memoryMap

#### F.7.78.24 setFieldSliceMemoryRemapRef

Description: Sets the memoryRemapRef on a fieldSlice element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldSliceID of type String - Handle to an fieldSlice element
— Input: memoryRemapRef of type String - Name of the referenced memoryRemap

#### F.7.78.25 setFieldSliceRange

Description: Sets a range on the given fieldSlice element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldSliceID of type String - Handle to a fieldSlice element
— Input: range of type String[] - Range, defined as a pair of left and right value expressions

#### F.7.78.26 setFieldSliceRegisterRef

Description: Sets the registerRef of a fieldSlice element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldSliceID of type String - Handle to a fieldSlice element
— Input: registerRef of type String - Name of the referenced register

#### F.7.78.27 setPortSlicePartSelect

Description: Set a partSelect on the given portSlice element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: portSliceID of type String - Handle to a portMap portSlice element
— Input: range of type String[] - Create the range on the partSelect with “left” for range[0] and “right” for range[1]. Set to null if you only want indices.
— Input: indices of type String[] - Handle to values of type String. Set all the index on the partSelect

#### F.7.78.28 setPortSlicePortRef

Description: Sets the portRef on a portSlice element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: portSliceID of type String - Handle to a portSlice element
— Input: portRef of type String - Name of the referenced port

#### F.7.78.29 setSliceRange

Description: Sets the range to the given range for the given slice element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: sliceID of type String - Handle to a slice element
— Input: range of type String[] - Range with left at index 0 and right at index 1

### F.7.79 Top element (BASE)

#### F.7.79.1 getAbstractionDefIDs

Description: Returns the handles to all the registered abstractionDefinition objects.

— Returns: abstractionDefIDs of type String - List of handles to abstractionDefinition objects

#### F.7.79.2 getAbstractorIDs

Description: Returns the handles to all the registered abstractor objects.

— Returns: abstractorIDs of type String - List of handles to abstractor objects

#### F.7.79.3 getBusDefIDs

Description: Returns the handles to all the registered busDefinition objects.

— Returns: busDefIDs of type String - List of handles to busDefinition objects

#### F.7.79.4 getCatalogIDs

Description: Returns the handles to all the registered catalog objects.

— Returns: catalogIDs of type String - List of handles to catalog objects

#### F.7.79.5 getComponentIDs

Description: Returns the handles to all the registered component objects.

— Returns: componentIDs of type String - List of handles to component objects

#### F.7.79.6 getDesignConfigurationIDs

Description: Returns the handles to all the registered designConfiguration objects.

— Returns: designConfigurationIDs of type String - List of handles to designConfiguration objects

#### F.7.79.7 getDesignIDs

Description: Returns the handles to all the registered design objects.

— Returns: designIDs of type String - List of handles to design objects

#### F.7.79.8 getGeneratorChainIDs

Description: Returns the handles to all the registered generatorChain objects.

— Returns: generatorChainIDs of type String - List of handles to generatorChain objects

#### F.7.79.9 getID

Description: Returns the handle to the object correspondintg to the given VLNV.

— Returns: rootObjectID of type String - Handle to the object with the given VLNV
— Input: VLNV of type String[] - The VLNV of the root object

#### F.7.79.10 getTypeDefinitionsIDs

Description: Returns the handles to all the registered typeDefinitions objects.

— Returns: typeDefinitionsIDs of type String - List of handles to typeDefinitions objects

#### F.7.79.11 getVLNV

Description: Returns the VLNV of the object with the given ID.

— Returns: VLNV of type String - The VLNV of the object with the given ID
— Input: rootObjectID of type String - Handle to a root object

#### F.7.79.12 getXMLPath

Description: Returns the location of the XML file that is registered with the VLNV of the given object.

— Returns: path of type String - The location of the XML file
— Input: rootObjectID of type String - Handle to a root object
— Input: dereference of type Boolean - True if the links have to be dereferenced

### F.7.80 Top element (EXTENDED)

#### F.7.80.1 createAbstractionDef

Description: Creates a new abstractionDef with the given VLNV, busDefVLNV, logicalName and type and
returns its abstractionDefID; fails and returns null if VLNV already exists.

— Returns: abstractionDefID of type String - Handle to a new abstractionDef element
— Input: abstractionDefVLNV of type String[] - abstractionDef VLNV
— Input: busDefVLNV of type String[] - busDef VLNV
— Input: logicalName of type String - Logical port name
— Input: type of type String - Logical port style (wire or transactional)

#### F.7.80.2 createAbstractor

Description: Creates a new abstractor with the given VLNV and returns its abstractorID; fails and returns
null if VLNV already exists.

— Returns: abstractorID of type String - Handle to a new abstractor
— Input: vlnv of type String[] - VLNV for a new abstractor
— Input: mode of type String - Abstractor mode
— Input: busDefVLNV of type String[] - busDef VLNV
— Input: firstBusInterfaceName of type String - First busInterface name
— Input: secondBusInterfaceName of type String - Second busInterfaceName

#### F.7.80.3 createBusDefinition

Description: Creates a new busDef with the given VLNV, directConnection, and isAddressable and returns
its busDefID; fails and returns null if VLNV already exists.

— Returns: busDefID of type String - Handle to a new busDef element
— Input: vlnv of type String[] - busDef VLNV
— Input: directConnection of type Boolean - busDef directionConnection
— Input: isAddressable of type Boolean - busDef isAddressable

#### F.7.80.4 createCatalog

Description: Creates a new catalog and returns its catalogID; fails and returns null if VLNV already exists.

— Returns: catalogID of type String - Handle to a new catalog element
— Input: vlnv of type String[] - Catalog VLNV

#### F.7.80.5 createComponent

Description: Creates a new component with the given VLNV and returns its componentID; fails and returns
null if VLNV already exists.

— Returns: componentID of type String - Handle to a new component
— Input: vlnv of type String[] - VLNV for a new component

#### F.7.80.6 createDesign

Description: Creates a new design with the given VLNV and returns its designID; fails and returns null if
VLNV already exists.

— Returns: designID of type String - Handle to a design element
— Input: vlnv of type String[] - Design VLNV

#### F.7.80.7 createDesignConfiguration

Description: Creates a new designConfiguration with the given VLNV and returns its designID; fails and
returns null if VLNV already exists.

— Returns: designConfigurationID of type String - Handle to a designConfiguration element
— Input: vlnv of type String[] - designConfiguration VLNV

#### F.7.80.8 createGeneratorChain

Description: Creates a new generatorChain with the given VLNV and returns its generatorChainID; fails and
returns null if VLNV already exists.

— Returns: generatorChainID of type String - Handle to a new generatorChain element
— Input: generatorChainVLNV of type String[] - generatorChain VLNV
— Input: generatorName of type String - The name value to be set on the generator
— Input: generatorExe of type String - The generatorExe value to be set

#### F.7.80.9 createTypeDefinitions

Description: Creates a new typeDefinitions with the given VLNV and returns its typeDefinitionsID; fails
and returns null if VLNV already exists.

— Returns: typeDefinitionsID of type String - Handle to the added typeDefinitions
— Input: typeDefinitionsVLNV of type String[] - VLNV for a new typeDefinitions

#### F.7.80.10 edit

Description: Signal start of editing of the given top-element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: rootObjectID of type String - Handle to a top-level element

#### F.7.80.11 setXMLPath

Description: Sets new location for the XML file that is registered with the VLNV of the given top-element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: rootObjectID of type String - Handle to a top-level element
— Input: path of type String - New location of XML file

### F.7.81 Type definitions (BASE)

#### F.7.81.1 getAddressBlockDefinitionAddressUnitBits

Description: Returns the addressUnitBits (resolved) value defined on the given addressBlockDefinition
element.

— Returns: addressUnitBits of type Long - The addressUnitBits value
— Input: addressBlockDefinitionID of type String - Handle to an addressBlockDefinition element

#### F.7.81.2 getAddressBlockDefinitionAddressUnitBitsExpression

Description: Returns the addressUnitBits expression defined on the given addressBlockDefinition element.

— Returns: addressUnitBits of type String - The addressUnitBits expression
— Input: addressBlockDefinitionID of type String - Handle to an addressBlockDefinition element

#### F.7.81.3 getAddressBlockDefinitionAddressUnitBitsID

Description: Returns the handle to the addressUnitBits defined on the given addressBlockDefinition
element.

— Returns: addressUnitBitsID of type String - Handle to the addressUnitBits element
— Input: addressBlockDefinitionID of type String - Handle to an addressBlockDefinition element

#### F.7.81.4 getBankDefinitionAddressUnitBits

Description: Returns the addressUnitBits (resolved) value defined on the given bankDefinition element.

— Returns: addressUnitBits of type Long - The addressUnitBits value
— Input: bankDefinitionID of type String - Handle to an bankDefinition element

#### F.7.81.5 getBankDefinitionAddressUnitBitsExpression

Description: Returns the addressUnitBits expression defined on the given bankDefinition element.

— Returns: addressUnitBits of type String - The addressUnitBits expression
— Input: bankDefinitionID of type String - Handle to an bankDefinition element

#### F.7.81.6 getBankDefinitionAddressUnitBitsID

Description: Returns the handle to the addressUnitBits defined on the given bankDefinition element.

— Returns: addressUnitBitsID of type String - Handle to the addressUnitBits element
— Input: bankDefinitionID of type String - Handle to an bankDefinition element

#### F.7.81.7 getEnumerationDefinitionEnumeratedValueIDs

Description: Returns the handles of all the enumeratedValues defined on the given enumerationDefinition
element.

— Returns: enumeratedValueIDs of type String - List of handles to the enumeratedValue elements
— Input: enumerationDefinitionID of type String - Handle to an enumerationDefinition element

#### F.7.81.8 getEnumerationDefinitionWidth

Description: Returns the (resolved) width value defined on the given enumerationDefinition element.

— Returns: width of type Long - The value of the width element
— Input: enumerationDefinitionID of type String - Handle to an enumerationDefinition element

#### F.7.81.9 getEnumerationDefinitionWidthExpression

Description: Returns the width expression defined on the given enumerationDefinition element.

— Returns: width of type String - The width expression
— Input: enumerationDefinitionID of type String - Handle to an enumerationDefinition element

#### F.7.81.10 getEnumerationDefinitionWidthID

Description: Returns the handle to the width element defined on the given enumerationDefinition element.

— Returns: widthID of type String - Handle to the width element
— Input: enumerationDefinitionID of type String - Handle to an enumerationDefinition element

#### F.7.81.11 getExternalTypeDefinitionsModeLinksIDs

Description: Returns the handles to all the modeLinks defined on the given externalTypeDefinitions
element.

— Returns: modeLinksIDs of type String - List of handles to the modeLinks elements
— Input: externalTypeDefinitionsID of type String - Handle to an externalTypeDefinitions element

#### F.7.81.12 getExternalTypeDefinitionsResetTypeLinkIDs

Description: Returns the handles to all the resetTypeLinks defined on the given externalTypeDefinitions
element.

— Returns: resetTypeLinksIDs of type String - List of handles to the resetTypeLinks elements
— Input: externalTypeDefinitionsID of type String - Handle to an externalTypeDefinitions element

#### F.7.81.13 getExternalTypeDefinitionsTypeDefinitionsRefByID

Description: Returns the handle to the typeDefinitions instance referenced from the given
externalTypeDefinitions.

— Returns: typeDefinitionsID of type String - Handle to the referenced typeDefinitions object
— Input: externalTypeDefinitionsID of type String - Handle to an externalTypeDefinitions element

#### F.7.81.14 getExternalTypeDefinitionsTypeDefinitionsRefByVLNV

Description: Returns the VLNV of the typeDefinitions referenced from the given externalTypeDefinitions.

— Returns: VLNV of type String - The VLNV of the referenced typeDefinitions object
— Input: externalTypeDefinitionsID of type String - Handle to an externalTypeDefinitions element

#### F.7.81.15 getExternalTypeDefinitionsViewLinkIDs

Description: Returns the handles to all the viewLinks defined on the given externalTypeDefinitions element

— Returns: viewLinkIDs of type String - List of handles to the viewLinks elements
— Input: externalTypeDefinitionsID of type String - Handle to an externalTypeDefitions element

#### F.7.81.16 getMemoryRemapDefinitionAddressUnitBits

Description: Returns the addressUnitBits (resolved) value defined on the given memoryRemapDefinition
element.

— Returns: addressUnitBits of type Long - The addressUnitBits value
— Input: memoryRemapDefinitionID of type String - Handle to an memoryRemapDefinition element

#### F.7.81.17 getMemoryRemapDefinitionAddressUnitBitsExpression

Description: Returns the addressUnitBits expression defined on the given memoryRemapDefinition
element.

— Returns: addressUnitBits of type String - The addressUnitBits expression
— Input: memoryRemapDefinitionID of type String - Handle to an memoryRemapDefinition element

#### F.7.81.18 getMemoryRemapDefinitionAddressUnitBitsID

Description: Returns the handle to the addressUnitBits defined on the given memoryRemapDefinition
element.

— Returns: addressUnitBitsID of type String - Handle to the addressUnitBits element
— Input: memoryRemapDefinitionID of type String - Handle to an memoryRemapDefinition element

#### F.7.81.19 getModeLinkExternalModeReferenceRefByName

Description: Returns the externalModeReference defined on the given modeLink element.

— Returns: externalModeReference of type String - The referenced externalMode name
— Input: modeLinkID of type String - Handle to a modeLink element

#### F.7.81.20 getModeLinkExternalModeReferenceID

Description: Returns the handle to the externalModeReference defined on the given modeLink element.

— Returns: externalModeReferenceID of type String - Handle to the externalModeReference element
— Input: modeLinkID of type String - Handle to a modeLink element

#### F.7.81.21 getModeLinkModeReferenceRefByName

Description: Returns the modeReference defined on the given modeLink element.

— Returns: modeReference of type String - The referenced mode name
— Input: modeLinkID of type String - Handle to a modeLink element

#### F.7.81.22 getModeLinkModeReferenceID

Description: Returns the handle to the modeReference defined on the given modeLink element.

— Returns: modeReferenceID of type String - Handle to the modeReference element
— Input: modeLinkID of type String - Handle to a modeLink element

#### F.7.81.23 getRegisterFileDefinitionAddressUnitBits

Description: Returns the addressUnitBits (resolved) value defined on the given registerFileDefinition
element.

— Returns: addressUnitBits of type Long - The addressUnitBits value
— Input: registerFileDefinitionID of type String - Handle to a registerFileDefinition element

#### F.7.81.24 getRegisterFileDefinitionAddressUnitBitsExpression

Description: Returns the addressUnitBits expression defined on the given registerFileDefinition element.

— Returns: addressUnitBits of type String - The addressUnitBits expression
— Input: registerFileDefinitionID of type String - Handle to a registerFileDefinition element

#### F.7.81.25 getRegisterFileDefinitionAddressUnitBitsID

Description: Returns the handle to the addressUnitBits defined on the given registerFileDefinition element.

— Returns: addressUnitBitsID of type String - Handle to the addressUnitBits element
— Input: registerFileDefinitionID of type String - Handle to a registerFileDefinition element

#### F.7.81.26 getResetTypeLinkExternalResetTypeRefByName

Description: Returns the externalResetTypeRef defined on the given resetTypeLink element.

— Returns: externalResetTypeRef of type String - The referenced externalResetType
— Input: resetTypeLinkID of type String - Handle to a resetTypeLink element

#### F.7.81.27 getResetTypeLinkExternalResetTypeReferenceID

Description: Returns the handle to the externalResetTypeReference defined on the given resetTypeLink
element.

— Returns: externalResetTypeReferenceID of type String - Handle to the externalResetTypeReference element
— Input: resetTypeLinkID of type String - Handle to a resetTypeLink element

#### F.7.81.28 getResetTypeLinkResetTypeReferenceRefByName

Description: Returns the resetTypeReference defined on the given resetTypeLink element.

— Returns: resetTypeReference of type String - The referenced resetType
— Input: resetTypeLinkID of type String - Handle to a resetTypeLink element

#### F.7.81.29 getResetTypeLinkResetTypeReferenceID

Description: Returns the handle to the resetTypeReference defined on the given resetTypeLink element.

— Returns: resetTypeReferenceID of type String - Handle to the resetTypeReference element
— Input: resetTypeLinkID of type String - Handle to a resetTypeLink element

#### F.7.81.30 getTypeDefinitionsAddressBlockDefinitionIDs

Description: Returns the handles to all the addressBlockDefinitions defined on the given typeDefinition
element.

— Returns: addressBlockDefinitionIDs of type String - List of handles to the addressBlockDefinition elements
— Input: typeDefinitionsID of type String - Handle to a typeDefinitions element

#### F.7.81.31 getTypeDefinitionsBankDefinitionIDs

Description: Returns the handles to all the bankDefinitions defined on the given typeDefinitions element.

— Returns: bankDefinitionIDs of type String - List of handles to the bankDefinition elements
— Input: typeDefinitionsID of type String - Handle to a typeDefinitions element

#### F.7.81.32 getTypeDefinitionsChoiceIDs

Description: Returns the handles to all the choices defined on the given typeDefinitions element.

— Returns: choiceIDs of type String - List of handles to choice elements
— Input: typeDefinitionsID of type String - Handle to a typeDefinitions element

#### F.7.81.33 getTypeDefinitionsEnumerationDefinitionIDs

Description: Returns the handles to all the enumerationDefinitions defined on the given typeDefinitions
element.

— Returns: enumerationDefinitionIDs of type String - List of handles to enumerationDefinition elements
— Input: typeDefinitionsID of type String - Handle to a typeDefinitions element

#### F.7.81.34 getTypeDefinitionsExternalTypeDefinitionsIDs

Description: Returns the handles to all the externalTypeDefinitions defined on the given typeDefinitions
element.

— Returns: externalTypeDefinitionsIDs of type String - List of handles to the externalTypeDefinitions elements
— Input: typeDefinitionsID of type String - Handle to a typeDefinitions element

#### F.7.81.35 getTypeDefinitionsFieldDefinitionIDs

Description: Returns the handles to all the field definitions defined on the given typeDefinitions element.

— Returns: fieldDefinitionIDs of type String - List of handles to the fieldDefinition elements
— Input: typeDefinitionsID of type String - Handle to a typeDefinitions element

#### F.7.81.36 getTypeDefinitionsMemoryMapDefinitionIDs

Description: Returns the handles to all the memoryMapDefinitions defined on the given typeDefinitions
element.

— Returns: memoryMapDefinitionIDs of type String - List of handles to the memoryMapDefinition elements
— Input: typeDefinitionsID of type String - Handle to a typeDefinitions element

#### F.7.81.37 getTypeDefinitionsMemoryRemapDefinitionIDs

Description: Returns the handles to all the memoryRemapDefinitions defined on the given typeDefinitions
element.

— Returns: memoryRemapDefinitionIDs of type String - List of handles to the memoryRemapDefinition elements
— Input: typeDefinitionsID of type String - Handle to a typeDefinitions element

#### F.7.81.38 getTypeDefinitionsModeIDs

Description: Returns the handles to all the modes defined on the given typeDefinitions element.

— Returns: modeIDs of type String - List of handles to the mode elements
— Input: typeDefinitionsID of type String - Handle to a typeDefinitions element

#### F.7.81.39 getTypeDefinitionsRegisterDefinitionIDs

Description: Returns the handles to all the registerDefinitions defined on the given typeDefinitions object.

— Returns: registerDefinitionIDs of type String - List of handles to the registerDefinition elements
— Input: typeDefinitionsID of type String - Handle to a typeDefintions element

#### F.7.81.40 getTypeDefinitionsRegisterFileDefinitionIDs

Description: Returns the handles to all the RegisterFileDefinitions defined on the given typeDefinition
element.

— Returns: registerFileDefinitionIDs of type String - List of handles to the register- FileDefinition elements
— Input: typeDefinitionsID of type String - Handle to a typeDefinitions element

#### F.7.81.41 getTypeDefinitionsResetTypeIDs

Description: Returns the handles to all the resetTypes defined on the given typeDefinitions element.

— Returns: resetTypesIDs of type String - List of handles to the resetTypes elements
— Input: typeDefinitionsID of type String - Handle to a typeDefinitions element

#### F.7.81.42 getTypeDefinitionsViewIDs

Description: Returns the handles to all the views defined on the given typeDefinitions element.

— Returns: viewIDs of type String - List of handles to the view elements
— Input: typeDefinitionsID of type String - Handle to a typeDefinitions element

#### F.7.81.43 getViewLinkExternalViewReferenceRefByName

Description: Returns the externalViewReference from the given viewLink element.

— Returns: externalViewReference of type String - The referenced externalView
— Input: viewLinkID of type String - Handle to a viewLink element

#### F.7.81.44 getViewLinkExternalViewReferenceID

Description: Returns the handle to the externalViewReference defined on the given viewLink element.

— Returns: externalViewReferenceID of type String - Handle to the externalViewReference element
— Input: viewLinkID of type String - Handle to a viewLink element

#### F.7.81.45 getViewLinkViewReferenceRefByID

Description: Returns the handle to the view referenced from the given viewLink element.

— Returns: viewID of type String - Handle to the referenced view element
— Input: viewLinkID of type String - Handle to a viewLink element

#### F.7.81.46 getViewLinkViewReferenceRefByName

Description: Returns the view referenced from the given viewLink element.

— Returns: viewRef of type String - The referenced view
— Input: viewLinkID of type String - Handle to a viewLink element

#### F.7.81.47 getViewLinkViewReferenceID

Description: Returns the handle to the viewReference defined on the given viewLink element.

— Returns: viewReferenceID of type String - Handle to the viewReference element
— Input: viewLinkID of type String - Handle to a viewLink element

### F.7.82 Type definitions (EXTENDED)

#### F.7.82.1 addComponentExternalTypeDefinitions

Description: Adds a new ExternalTypeDefinitions to the given component.

— Returns: externalDefinitionsID of type String - The identifier of the added ExternalDefinitions
— Input: componentID of type String - Handle to the component type
— Input: name of type String - Name of the external type definition
— Input: vlnv of type String[] - Handle to the external type definition’s VLNV

#### F.7.82.2 addEnumerationDefinition

Description: Adds an EnumerationDefiniton to a ComponentType’s EnumerationDefinitions and creates an
underlying enumerated value.

— Returns: EnumerationDefinitionID of type String - Handle to the added EnumerationDefinition
— Input: typeDefID of type String - Handle to typeDef element
— Input: name of type String - Name of the new enumeration definition
— Input: enumeratedName of type String - Name of the (first) new enumeratedValue
— Input: enumeratedExpression of type String - Expression associatd with the (first) new enumeratedValue

#### F.7.82.3 addEnumerationDefinitionEnumeratedValue

Description: Adds an EnumeratedValue to the given EnumerationDefinition element.

— Returns: EnumeratedValueID of type String - Handle to the added EnumeratedValue
— Input: enumerationDefinitionID of type String - Handle to an EnumerationDefinition
— Input: name of type String - Name of the new EnumeratedValue
— Input: value of type String - Expression of the new EnumeratedValue

#### F.7.82.4 addExternalTypeDefinitionsModeLink

Description: Adds the given modeLink in the given externalTypeDefinitions element.

— Returns: modeLinkID of type String - Handle to the added modeLink
— Input: externalTypeDefinitionsID of type String - Handle to an externalTypeDefinitions element
— Input: externalModeRef of type String - Name of the referenced external mode
— Input: modeReference of type String - the modeReferences to be add on the modeLink

#### F.7.82.5 addExternalTypeDefinitionsViewLink

Description: Adds the given viewLink in the given externalTypeDefinitions element.

— Returns: viewLinkID of type String - Handle to a viewLink element
— Input: externalTypeDefinitionsID of type String - Handle to an externalTypeDefinitions element
— Input: externalViewRef of type String - Name of the referenced external view
— Input: viewReference of type String - Name of the referenced view

#### F.7.82.6 addFieldDefinitionsEnumeratedValue

Description: Adds an enumerated value (name, value pair) to the given Field definition.

— Returns: enumeratedValueID of type String - The identifier of the added EnumeratedValue
— Input: fieldDefinitionID of type String - Handle to the fieldDefinition
— Input: name of type String - EnumeratedValue name
— Input: expression of type String - EnumeratedValue value expression

#### F.7.82.7 addTypeDefinitionsAddressBlockDefinition

Description: Adds an AddressBlockDefinition to a ComponentType's AddressBlockDefinitions and creates
an underlying enumerated value.

— Returns: addressBlockDefinitionID of type String - Handle to the added AddressBlockDefinition
— Input: typeDefinitionsID of type String - Handle to typeDefinitions element
— Input: name of type String - Name of the new AddressBlockDefinition
— Input: range of type String - Range of the new AddressBlockDefinition
— Input: width of type String - Width of the new AddressBlockDefinition

#### F.7.82.8 addTypeDefinitionsBankDefinition

Description: Adds a bankDefinition to a typeDefinitions element.

— Returns: bankDefinitionID of type String - Handle to the added bankDefinition
— Input: typeDefinitionsID of type String - Handle to a typeDefinitions object
— Input: name of type String - Handle to a bankDefinition name

#### F.7.82.9 addTypeDefinitionsChoice

Description: Adds a choice with the given name and enumerations to the given type definitions element.

— Returns: choiceID of type String - Handle to a new choice
— Input: typeDefinitionsID of type String - Handle to a type definitions element
— Input: name of type String - Choice name
— Input: enumerations of type String[] - List of enumeration values

#### F.7.82.10 addTypeDefinitionsEnumerationDefinition

Description: Adds an enumerationDefinition to a typeDefinitions element.

— Returns: enumerationDefinitionID of type String - Handle to the added enumerationDefinition
— Input: typeDefinitionsID of type String - Handle to a typeDefinitions element
— Input: name of type String - EnumerationDefinition name
— Input: width of type String - width expression

#### F.7.82.11 addTypeDefinitionsExternalTypeDefinitions

Description: Adds an externalTypeDefinitions.

— Returns: externalTypeDefinitionsID of type String - Handle to the added externalTypeDefinitions
— Input: typeDefinitionsID of type String - Handle to the typeDefinitions
— Input: name of type String - Handle to an externalTypeDefinitions element
— Input: vlnv of type String[] - VLNV of the referenced typeDefinitions element

#### F.7.82.12 addTypeDefinitionsFieldAccessPolicyDefinition

Description: Adds a fieldAccessPolicyDefinition to a typeDefinitions element.

— Returns: fieldAccessPolicyDefinitionID of type String - Handle to the added fieldAccessPolicyDefinition
— Input: typeDefinitionsID of type String - Handle to a typeDefinitions element
— Input: name of type String - Handle to a fieldAccessPolicyDefinition name

#### F.7.82.13 addTypeDefinitionsFieldDefinition

Description: Adds a fieldDefinition to a component type.

— Returns: fieldDefinitionID of type String - Handle to the added fieldDefinition or null if the call failed
— Input: typeDefinitionsID of type String - Handle to the typeDefinitions type
— Input: name of type String - Handle to the name of the field definition
— Input: bitWidth of type String - Handle to the bitWidth expression associated with the field definition

#### F.7.82.14 addTypeDefinitionsMemoryMapDefinition

Description: Adds a memoryMapDefinition on the containing element.

— Returns: memoryMapDefinitionID of type String - The identifier of the added memoryMapDefinition
— Input: typeDefinitionsID of type String - Handle to a typeDefinitions element
— Input: name of type String - Name of the memoryMap

#### F.7.82.15 addTypeDefinitionsMemoryRemapDefinition

Description: Adds a memoryRemapDefinition to a typeDefinitions element.

— Returns: memoryRemapDefinitionID of type String - Handle to the added memoryRemapDefinition
— Input: typeDefinitionsID of type String - Handle to a typeDefinitions element
— Input: name of type String - Handle to a memoryRemapDefinition name

#### F.7.82.16 addTypeDefinitionsMode

Description: Adds a mode to the given typeDefinitions element.

— Returns: modeID of type String - Handle to the added mode
— Input: typeDefinitionsID of type String - Handle to a typeDefinitions element
— Input: name of type String - Handle to Mode name

#### F.7.82.17 addTypeDefinitionsRegisterDefinition

Description: Adds a registerDefinition to a typeDefinition element.

— Returns: registerDefinitionID of type String - Handle of registerDefinition element
— Input: typeDefinitionsID of type String - Handle to a typeDefinitions element
— Input: name of type String - Handle to the registerDefintion name
— Input: size of type String - The value of the attribute Size
— Input: fieldName of type String - Field name
— Input: fieldOffset of type String - Field offset
— Input: fieldWidth of type String - Field width

#### F.7.82.18 addTypeDefinitionsRegisterFileDefinition

Description: Adds a registerFileDefinition to the given typeDefinitions element.

— Returns: registerFileDefinitionID of type String - Handle to the registerFileDefinition
— Input: typeDefinitionsID of type String - The identifier of a typeDefinitions
— Input: name of type String - The name of the RegisterFileDefinition to create
— Input: range of type String - The range expression associated with the registerFileDefinition to be created

#### F.7.82.19 addTypeDefinitionsResetType

Description: Adds a resetType on the given typeDefinition.

— Returns: resetTypeID of type String - ID of the created resetType
— Input: typeDefinitionsID of type String - Handle to a typeDefinitions type
— Input: name of type String - Handle to the created resetType name

#### F.7.82.20 addTypeDefinitionsView

Description: Adds a view to the given typeDefinitions element.

— Returns: viewID of type String - Handle to the added view
— Input: typeDefinitionsID of type String - Handle to a typeDefinitions element
— Input: name of type String - Handle to Mode name

#### F.7.82.21 removeAddressBlockDefinitionAddressUnitBits

Description: Removes the addressUnitBits on an addressBlockDefinitionRef

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressBlockDefinitionID of type String - Handle to an addressBlockDefinition element

#### F.7.82.22 removeBankDefinitionAddressUnitBits

Description: Removes the addressUnitBits field of the given bankDefinition element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: bankDefinitionID of type String - Handle to a bankDefinition

#### F.7.82.23 removeComponentExternalTypeDefinitions

Description: Removes the given externalTypeDefinitions form the containing component element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: externalTypeDefinitionsID of type String - Handle to an externalTypeDefinitions element

#### F.7.82.24 removeEnumerationDefinitionEnumeratedValue

Description: Removes the given enumeratedValue from its containing enumerationDefinition element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: enumeratedValueID of type String - Handle to an enumeratedValue element

#### F.7.82.25 removeExternalTypeDefinitionsModeLink

Description: Removes the given modeLink from its containing externalTypeDefinitions element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: modeLinkID of type String - Handle to a modeLink element

#### F.7.82.26 removeExternalTypeDefinitionsResetTypeLink

Description: Removes the given resetLink from its containing externalTypeDefinitions element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: resetTypeLinkID of type String - Handle to a resetTypeLink element

#### F.7.82.27 removeExternalTypeDefinitionsViewLink

Description: Removes the given viewLink from its containing externalTypeDefinitions element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: viewLinkID of type String - Handle to a viewLink element

#### F.7.82.28 removeFieldDefinitionEnumerationDefinitionRef

Description: Removes the enumerationDefinitionRef from its containing fieldDefinition element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldDefinitionID of type String - Handle to the enumerationDefinition

#### F.7.82.29 removeFieldDefinitionsEnumeratedValue

Description: Removes the given enumeratedValue from its containing fieldDefinitions element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: domainTypeDefID of type String - Handle to a domainTypeDef element

#### F.7.82.30 removeMemoryRemapDefinitionAddressUnitBits

Description: Removes the addressUnitBits field of the given memoryRemapDefinition element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: memoryRemapDefinitionID of type String - Handle to a memoryRemapDefinition

#### F.7.82.31 removeRegisterFileDefinitionAddressUnitBits

Description: Removes the addressUnitBits field of the given registerFileDefinition element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerFileDefinitionID of type String - Handle to a registerFileDefinition

#### F.7.82.32 removeTypeDefinitionsAddressBlockDefinition

Description: Removes the given addressBlockDefinition from its containing typeDefinitions element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressBlockDefinitionID of type String - Handle to an addressBlockDefinition object

#### F.7.82.33 removeTypeDefinitionsBankDefinition

Description: Removes the given bankDefinition from its containing typeDefinitions element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: bankDefinitionID of type String - Handle to a bankDefinition element

#### F.7.82.34 removeTypeDefinitionsChoice

Description: Removes the given choice element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: choiceID of type String - Handle to a choice element

#### F.7.82.35 removeTypeDefinitionsEnumerationDefinition

Description: Removes the given enumerationDefinition from its containing typeDefinitions element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: enumerationDefinitionID of type String - Handle to an enumerationDefinition element

#### F.7.82.36 removeTypeDefinitionsExternalTypeDefinitions

Description: Removes the given externalTypeDefinitions from its containing typeDefinitions element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: externalTypeDefinitionsID of type String - Handle to the externalTypeDefinitions

#### F.7.82.37 removeTypeDefinitionsFieldAccessPolicyDefinition

Description: Removes the given fieldAccessPolicyDefinition from its containing typeDefinitions element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldAccessPolicyDefinitionID of type String - Handle to a fieldAccessPolicyDefinition element

#### F.7.82.38 removeTypeDefinitionsFieldDefinition

Description: Removes the given fieldDefinition from its containing typeDefinitions element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: fieldDefinitionID of type String - Handle to a fieldDefinition element

#### F.7.82.39 removeTypeDefinitionsMemoryMapDefinition

Description: Removes the given memoryMapDefinition from its containing typeDefinitions element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: memoryMapDefinitionID of type String - Handle to the aimed item

#### F.7.82.40 removeTypeDefinitionsMemoryRemapDefinition

Description: Removes the given memoryRemapDefinition from its containing typeDefinitions element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: memoryRemapDefinitionID of type String - Handle to a memoryRemapDefinition element

#### F.7.82.41 removeTypeDefinitionsMode

Description: Removes the given mode from its containing typeDefinitions element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: modeID of type String - Handle to a mode element

#### F.7.82.42 removeTypeDefinitionsRegisterDefinition

Description: Removes the given registerDefinition from its containing typeDefinitions element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerDefinitionID of type String - Handle to a registerDefinition

#### F.7.82.43 removeTypeDefinitionsRegisterFileDefinition

Description: Removes the given registerFileDefinition from its containing type definitions element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerFileDefinitionID of type String - Handle to a registerFileDefinition element

#### F.7.82.44 removeTypeDefinitionsResetType

Description: Removes the given resetType from its containing TypeDefinitions element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: resetTypeID of type String - Handle to the resetType element

#### F.7.82.45 removeTypeDefinitionsView

Description: Removes the given view from its containing typeDefinitions object.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: viewID of type String - Handle to a view element

#### F.7.82.46 setAddressBlockDefinitionAddressUnitBits

Description: Sets the addressUnitBits on an addressBlockDefinitionRef.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: addressBlockDefinitionID of type String - Handle to an addressBlockDefinition element
— Input: addressUnitBits of type String - The addressUnitBits expression

#### F.7.82.47 setBankDefinitionAddressUnitBits

Description: Sets the addressUnitBits field of the given bankDefinition element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: bankDefinitionID of type String - Handle to a bankDefinition
— Input: addressUnitBits of type String - Handle to the new value for the addressUnitBits field (expression / string)

#### F.7.82.48 setEnumerationDefinitionWidth

Description: Sets the width field of the given enumerationDefinition element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: enumerationDefinitionID of type String - Handle to a typeDefinitions element
— Input: width of type String - Handle to the new value for the width field (expression/string)

#### F.7.82.49 setExternalTypeDefinitionsTypeDefinitionsRef

Description: Sets the typeDefinitionsRef on the externalTypeDefinitions.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: externalTypeDefinitionsID of type String - Handle to an externalTypeDefinitions element
— Input: typeDefinitionsRef of type String[] - VLNV of the referenced typeDefinitions object

#### F.7.82.50 setMemoryRemapDefinitionAddressUnitBits

Description: Sets the addressUnitBits field of the given memoryRemapDefinition element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: memoryRemapDefinitionID of type String - Handle to a memoryRemapDefinition
— Input: addressUnitBits of type String - Handle to the new value for the addressUnitBits field (expression / string)

#### F.7.82.51 setModeLinkExternalModeReference

Description: Sets the externalModeReference on a modeLink element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: modeLinkID of type String - Handle to a modeLink element
— Input: modeRef of type String - the modeRef value to set on the externalModeReference

#### F.7.82.52 setModeLinkModeReference

Description: Sets the modeReference on the given modeLink element

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: modeLinkID of type String - Handle to a modeLink element
— Input: modeRef of type String - Handle to a modeRef element

#### F.7.82.53 setRegisterFileDefinitionAddressUnitBits

Description: Sets the addressUnitBits field of the given registerFileDefinition element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: registerFileDefinitionID of type String - Handle to a registerFileDefinition
— Input: addressUnitBits of type String - Handle to the new value for the addressUnitBits field (expression / string)

#### F.7.82.54 setResetTypeLinkExternalResetTypeReference

Description: Sets the externalResetTypeReference of a resetTypeLink element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: resetTypeLinkID of type String - Handle to a resetTypeLink element
— Input: resetTypeRef of type String - the value of the resetTypeRef on the externalResetTypeReference

#### F.7.82.55 setResetTypeLinkResetTypeReference

Description: Sets the resetTypeReference on a resetTypeLink element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: resetTypeLinkID of type String - Handle to a resetTypeLink element
— Input: resetTypeRef of type String - the value of the resetTypeRef on the externalResetTypeReference

#### F.7.82.56 setViewLinkExternalViewReference

Description: Sets the externalViewReference on a viewLink elements

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: viewLinkID of type String - Handle to a viewLink element
— Input: viewRef of type String - The viewRef expression to be set on the externalViewReference

#### F.7.82.57 setViewLinkViewReference

Description: Sets the viewReference on a viewLink elements

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: viewLinkID of type String - Handle to a viewLink element
— Input: viewRef of type String - The viewRef expression to be set on the viewReference

### F.7.83 Vector (BASE)

#### F.7.83.1 getVectorIDs

Description: Returns the handles to all the vectors defined on the given element.

— Returns: vectorIDs of type String - List of handles to vector elements
— Input: vectorContainerID of type String - Handle to an element that has a vector element

#### F.7.83.2 getVectorLeftID

Description: Returns the handle to the left range of the given vector element.

— Returns: LeftID of type String - Handle to the left element
— Input: vectorID of type String - Handle to a vector element

#### F.7.83.3 getVectorRange

Description: Returns the range defined on the given vector element.

— Returns: range of type Long - Array of two range values: left and right
— Input: vectorID of type String - Handle to a vector element

#### F.7.83.4 getVectorRangeExpression

Description: Returns the range expressions defined on the given vector element.

— Returns: rangeExpression of type String - Array of two range expressions: left and right
— Input: vectorID of type String - Handle to a vector element

#### F.7.83.5 getVectorRightID

Description: Returns the handle to the right range of the given vector element.

— Returns: RightID of type String - Handle to the right element
— Input: vectorID of type String - Handle to a vector element

### F.7.84 Vector (EXTENDED)

#### F.7.84.1 addVector

Description: Adds a vector to the given element.

— Returns: vectorID of type String - Handle to new vector
— Input: vectorContainerElementID of type String - Handle to an element that has a vector element
— Input: range of type String[] - Range expression with left in index 0 and right in index 1

#### F.7.84.2 removeVector

Description: Removes the given vector.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: vectorID of type String - Handle to a vector element

### F.7.85 Vendor extensions (BASE)

#### F.7.85.1 getVendorExtensions

Description: Returns the handle to the vendorExtension defined on the given element.

— Returns: vendorExtensions of type String - Handle to the vendorExtension
— Input: vendorExtensionsContainerElementID of type String - Handle to an element that

has a vendor extension element

### F.7.86 Vendor extensions (EXTENDED)

#### F.7.86.1 addVendorExtensions

Description: Adds a vendor extension with given value to the given element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: vendorExtensionsContainerElementID of type String - Handle to an element that has a vendor extension element
— Input: vendorExtensions of type String - Vendor extension value

#### F.7.86.2 removeVendorExtensions

Description: Removes the given vendor extension.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: vendorExtensionsContainerElementID of type String - Handle to an element that

has a vendor extension element

#### F.7.86.3 setVendorExtensions

Description: Sets the vendorExtension XML string to given container element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: vendorExtensionsContainerElementID of type String - Handle to an element that has a vendor extension element
— Input: vendorExtensions of type String - Vendor extension value

### F.7.87 View (BASE)

#### F.7.87.1 getAbstractorInstanceViewNameRefByID

Description: Returns the handle to the view referenced from the given abstractorInstance element.

— Returns: viewID of type String - Handle to the referenced view element
— Input: abstractorInstanceID of type String - Handle to an abstractorInstance element

#### F.7.87.2 getViewComponentInstantiationRefByID

Description: Returns the handle to the componentInstantiation referenced from the given view element.

— Returns: componentInstantiationID of type String - Handle to the referenced componentInstantiation element
— Input: viewID of type String - Handle to the view element

#### F.7.87.3 getViewComponentInstantiationRefByName

Description: Returns the componentInstantiationRef from the given view element.

— Returns: componentInstantiationRef of type String - The referenced componentInstantiation name
— Input: viewID of type String - Handle to a view element

#### F.7.87.4 getViewDesignConfigurationInstantiationID

Description: Returns the handle to a designConfigurationInstantiation from the given view element.

— Returns: designConfigurationInstantiationID of type String - Handle to a designConfigurationInstantiation
— Input: viewID of type String - Handle to a view element

#### F.7.87.5 getViewDesignConfigurationInstantiationRefByID

Description: Returns the handle to the designConfigurationInstantiation referenced from the given view
element.

— Returns: designConfigurationInstantiationID of type String - Handle to the referenced designConfigurationInstantiation element
— Input: viewID of type String - Handle to a view element

#### F.7.87.6 getViewDesignConfigurationInstantiationRefByName

Description: Returns the designConfigurationInstantiationRef from the given view element.

— Returns: designConfigurationInstantiationRef of type String - The referenced designConfigurationInstantiation name
— Input: viewID of type String - Handle to a view element

#### F.7.87.7 getViewDesignInstantiationRefByID

Description: Returns the handle to the designInstantiation referenced from the given view element.

— Returns: designInstantiationID of type String - Handle to the referenced designInstantiation element
— Input: viewID of type String - Handle to the view element

#### F.7.87.8 getViewDesignInstantiationRefByName

Description: Returns the designInstantiation reference from the given view element.

— Returns: designInstantiationRef of type String - The referenced designInstantiation name
— Input: viewID of type String - Handle to a view element

#### F.7.87.9 getViewEnvIdentifierIDs

Description: Returns the handles to all the envIdentifiers from the given view element.

— Returns: envIdentifierIDs of type String - List of handles to the envIdentifier elements
— Input: viewID of type String - Handle to a view

#### F.7.87.10 getViewEnvIdentifiers

Description: Returns the envIdentifiers defined on the given view element.

— Returns: envIdentifier of type String - List of view envIdentifiers
— Input: viewID of type String - Handle to a view element

#### F.7.87.11 getViewRefByName

Description: Returns the view name defined on the given viewRef element.

— Returns: viewName of type String - The referenced view
— Input: viewRefID of type String - Handle to a viewRef element

### F.7.88 View (EXTENDED)

#### F.7.88.1 addViewEnvIdentifier

Description: Adds an envIdentifier on the given view of a component or on a view of an abstractor.

— Returns: envIdentifierID of type String - Handle to the added envIdentifier
— Input: viewID of type String - Handle to a view element
— Input: value of type String - Name of the envIdentifier

#### F.7.88.2 removeViewComponentInstantiationRef

Description: Removes componentInstantiationRef for the given view element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: viewID of type String - Handle to a view element

#### F.7.88.3 removeViewDesignConfigurationInstantiationRef

Description: Removes designConfigurationInstantiationRef for the given view element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: viewID of type String - Handle to a view element

#### F.7.88.4 removeViewDesignInstantiationRef

Description: Removes designInstantiationRef for the given view element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: viewID of type String - Handle to a view element

#### F.7.88.5 removeViewEnvIdentifier

Description: Removes the given envIdentifier from its containing a view element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: envIdentifierID of type String - Handle to an envIdentifier element

#### F.7.88.6 setViewComponentInstantiationRef

Description: Sets componentInstantiationRef for the given view element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: viewID of type String - Handle to a view element
— Input: componentInstantiationRef of type String - ComponentInstantiation name

#### F.7.88.7 setViewDesignConfigurationInstantiationRef

Description: Sets designConfigurationInstantiationRef for the given view element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: viewID of type String - Handle to a view element
— Input: designInstantiationRef of type String - designConfigurationInstantiation name

#### F.7.88.8 setViewDesignInstantiationRef

Description: Sets designInstantiationRef for the given view element.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: viewID of type String - Handle to a view element
— Input: designInstantiationRef of type String - designInstantiation name

#### F.7.88.9 setViewRefValue

Description: Sets the name of the viewRef.

— Returns: status of type Boolean - Indicates call is successful (true) or not (false)
— Input: viewRefID of type String - Handle to a viewRef element
— Input: value of type String - Name of the referenced view

### F.7.89 All ID types

This subclause lists the TGI ID types as follows:

— absDefOrAbsDefInstanceID
— absDefPortID
— abstractionDefID
— abstractionDefPortID
— abstractionDefPortModeID
— abstractionDefinitionID
— abstractionTypeID
— abstractorBusInterfaceID
— abstractorGeneratorID
— abstractorID
— abstractorInstanceID
— abstractorInstancesID
— abstractorInterfaceID
— abstractorOrAbstractorInstanceID
— abstractorViewIDaccessHandleID
— accessID
— accessPolicyID
— accessRestrictionID
— activeInterfaceID
— adHocConnectionID
— adHocExternalPortReferenceID
— adHocInternalPortReferenceID
— addressBlockDefinitionID
— addressBlockDefinitionRefID
— addressBlockID
— addressBlockRefID
— addressSpaceID
— addressSpaceRefID
— aliasOfID
— alternateRegisterID
— alternateRegisterRefID
— argumentID
— arraryID
— arrayContainerElementID
— arrayID
— arrayOrfieldArrayID
— assertionContainerElementID
— assertionID
— attributeContainerID
— bankDefinitionID
— bankID
— bankOrLocalBankID
— bankRefID
— bankrefID
— baseAddressesID
— broadcastToID
— buildCommandID
— busDefID
— busDefOrBusDefInstanceID
— busDefinitionID
— busInterfaceID
— busInterfaceRefID
— catalogID
— cellSpecificationID
— chainGroupID
— channelID
— choiceEnumerationID
— choiceID
— clearboxElementID
— clearboxElementRefID
— clearboxElementRefLocationID
— clearboxID clockDriverID
— clockPeriodID
— componentGeneratorID
— componentGeneratorSelectorID
— componentID
— componentInstanceID
— componentInstantiationID
— componentOrComponentInstanceID
— configurableElementID
— configurableElementValueID
— configuredElementID
— constraintSetID
— constraintSetRefID
— constraitSetID
— cpuID
— defaultFileBuilderID
— defineID
— dependencyID
— designConfID
— designConfigurationID
— designConfigurationInstantiationID
— designConfigurationOrDesignConfigurationInstanceID
— designID
— designInstantiationID
— dimID
— domainTypeDefID
— driveConstraintID
— driverID
— elementContainerID
— elementID
— enumeratedValueID
— enumeratedValuesID
— enumerationDefinitionID
— envIdentifierID
— excludePortID
— executableImageID
— exportedNameID
— expressionID
— externalPortReferenceID
— externalTypeDefinitionsID
— fieldAccessPoliciesID
— fieldAccessPolicyDefinitionID
— fieldAccessPolicyID
— fieldAccessPoliciesID
— fieldDefinitionID
— fieldID
— fieldMapID
— fieldRefID
— fieldSliceID
— fileBuilderID
— fileDefineID
— fileID
— fileSetID
— fileSetRefGroupID
— fileSetRefID
— fileTypeID
— functionID
— functionSourceFileID
— generatorChainConfigurationID
— generatorChainID
— generatorChainSelectorID
— generatorID
— generatorRefID
— groupID
— groupSelectorID
— groupSelectorNameID
— hierInterfaceID
— imageTypeID
— indexID
— indirectAddressRefID
— indirectDataRefID
— indirectInterfaceID
— initiatorID
— interconnectionConfigurationID
— interconnectionID
— interfaceRefID
— internalPortReferenceID
— ipxactFileID
— languageToolsID
— linkerCommandFileID
— loadConstraintID
— localMemoryMapID
— locationID
— logicalPortID
— memoryMapDefinitionID
— memoryMapElementID
— memoryMapID
— memoryMapOrLocalMemoryMapID
— memoryMapRefID
— memoryRemapDefinitionID
— memoryRemapID
— memoryMapID
— mirroredSystemID
— mirroredTargetID
— modeConstraintsID
— modeConstraintsID
— modeID
— modeLinkID
— modeRefID
— moduleOrTypeParameterContainerElementID
— moduleParameterID
— moduleParameterTypeID
— monitorID
— monitorInterconnectionID
— monitorInterfaceID
— monitoredActiveInterfaceID
— onSystemID
— otherClockDriverID
— packetFieldID
— packetID
— parameterBaseTypeID
— parameterContainerElementID
— parameterID
— parametizedID
— partSelectID
— pathSegmentID
— payLoadID
— payloadID
— physicalPortID
— portID
— portMapID
— portModeID
— portSliceID
— portWireID
— powerConstraintID
— powerDomainID
— powerDomainLinkID
— powerDomainRefID
— powerEnID
— protocolID
— qualifierID
— referenceID
— regFieldID
— regionID
— registerDefinitionID
— registerFieldID
— registerFileDefinitionID
— registerFileID
— registerFileRefID
— registerID
— registerRefID
— remapAddressID
— remapAddressesID
— resetID
— resetTypeID
— resetTypeLinkID
— rootObjectID
— segmentID
— serviceTypeDefID
— signalTypeDefID
— singleShotDriverID
— sliceID
— sourceFileID
— strucPortTypeDefID
— structPortTypeDefID
— structuredID
— subPortID
— subPortMapID
— subPortRefID
— subPortReferenceID
— subSpaceID
— subSpaceMapID
— subspaceMapID
— systemGroupNameID
— systemID
— targetID
— timingConstraintID
— transTypeDefID
— transactionalID
— transparentBridgeID
— transparentBrigeID
— transportMethodsID
— typeDefID
— typeDefinitionID
— typeDefinitionsID
— typeParameterID
— unconfiguredElementID
— vectorContainerElementID
— vectorContainerID
— vectorID
— vendorExtensionsContainerElementID
— viewConfigurationID
— viewConfigurationOrViewID
— viewID
— viewLinkID
— viewRefID
— wireID
— wireTypeDefID
— writeValueConstraintID
