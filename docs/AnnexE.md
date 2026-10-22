<style>
table {
    border-collapse: collapse;
}
table, th, td {
   /* border: 1px solid black; */
  border: 2px solid #333;
}
blockquote {
  border-left: solid blue;
  padding-left: 10px;
}
</style>

# Annex E — SystemVerilog expressions

(normative)

This standard utilizes SystemVerilog expressions as a means to specify an equation as the value of
an element.  Expressions can be specified for all predefined element values having an associated type (see
C.7 complexBaseExpression and C.21 parameters) that allows for an expression to be
specified.  Besides predefined types, parameters can also be
specified using expressions, in which case the type attributes define the type of expression that can be
specified.

## E.1 Overview
The IP-XACT Expression Language is based on the SystemVerilog Expression Language as specified in
IEEE Std 1800-2012.

The goal of the IP-XACT Expression Language is for it to be a subset of IEEE Std 1800-2012, i.e., the
expressions defined in IP-XACT should be easily ported-to or incorporated-into a SystemVerilog file and
interpreted by any SystemVerilog parser/processor.

The IP-XACT Expression Language, however, should also be able to represent constructs and functionality
specific to the IP-XACT language.  To make the language more in-line with the IP-XACT language, some
functionality has been limited and some changes to the original SystemVerilog Expression Language were
introduced.

(e2)=
## E.2 Data-types
A subset of the SystemVerilog data-types are used by the IP-XACT Expression Language. All IP-XACT
data-types map to a specific SystemVerilog data-type. The casting functionality and operators follow the
same subset of the functionality specified by the SystemVerilog Expression Language.
It has been decided to not support complex, user-defined, and time data-types in IP-XACT; it has also been
decided to support only two-state values and not allow for unknown or high-impedance values. Each

supported System Verilog data type also has a additional corresponding unresolved data type in the IP-
XACT Expression Language. The supported data-types are shown in [Table E.1](#table_e1).

(table_e1)=

*Table E.1—Data-types*
| Data-type  | Description                                 |
|------------|:--------------------------------------------|
| bit        | 2-state data type, user-defined vector size |
| byte       | 2-state data type, 8-bit signed integer     |
| shortint   | 2-state data type, 16-bit signed integer    |
| int        | 2-state data type, 32-bit signed integer    |
| longint    | 2-state data type, 64-bit signed integer    |
| shortreal  | 32-bit floating point                       |
| real       | 64-bit floating point                       |
| string     | An ordered collection of characters         |

### E.2.1 bit data type
The <span style="color:red">**bit**</span> data-type is equivalent to the **bit** data-type in SystemVerilog.

### E.2.2 byte data type
The <span style="color:red">**byte**</span> data-type is equivalent to the **byte** data-type in SystemVerilog, except it is not possible to specify
an ASCII character and, therefore, ASCII characters cannot be assigned to a **byte** variable.

### E.2.3 shortint data type
The <span style="color:red">**shortint**</span> data-type is equivalent to the **shortint** data-type in SystemVerilog.

### E.2.4 int data type
The <span style="color:red">**int**</span> data-type is equivalent to the **int** data-type in SystemVerilog.

### E.2.5 longint data type
The <span style="color:red">**longint**</span> data-type is equivalent to the **longint** data-type in SystemVerilog.

### E.2.6 shortreal data type
The <span style="color:red">**shortreal**</span> data-type is equivalent to the **shortreal** data-type in SystemVerilog.

### E.2.7 real data type
The <span style="color:red">**real**</span> data-type is equivalent to the <span style="color:red"> data-type in SystemVerilog.

### E.2.8 string data type
The IP-XACT Expression Language <span style="color:red">**string**,</span>. data-type is equivalent to the SystemVerilog **string** datatype;
just like the SystemVerilog **string**, it supports only US-ASCII characters.

To simplify the string functionality and avoid potential issues with string-length, indexing, and casting to
and from **long** or **bitstring** values, however, casting, indexing, and length tests are not supported. As a
result, an IP-XACT **string** can be seen as an immutable, 'simple' object without length, which cannot be cast
to other types or from other types. Also, only the string-equality, inequality, concatenation, replication, and
inside operators are supported (see  Table E.2 of the source standard).

### E.2.9 Signed and unsigned data types
The IP-XACT data-types follow the same default signed/unsigned functionality as has been defined in the
SystemVerilog Expression Language, i.e., the **bit** data-type is unsigned and the **byte**, **shortint**, **int**, and
**longint** data-types are signed by default.

IP-XACT also allows specifying the signed-ness when assigning the values. and just like in SystemVerilog,
the signed-ness can also be used when casting the value.

### E.2.10 Unresolved data types
The IP-XACT unresolved data-types represent expressions which cannot be calculated into a single known
value using only the information available in IP-XACT.  Each supported System Verilog data-type has a
corresponding unresolved data-type.  Such unresolved data-types are propagated through the IP-XACT
processing as unresolved expressions.  An expression has an unresolved data-type value if it includes a
function which returns a value with an unresolved data-type. Operators which have operands with values
with unresolved data-types and functions which have arguments with values with unresolved data-types
return a value with an unresolved data-type.  These expressions can only be resolved to a single known value
with additional information.  An example is a pathSegment element which has a unresolvedStringExpression
type and may contain a reference to an array index by including the $ipxact_index_value() function.  The
actual value for the array index would be provided by a generator when the pathSegment needs to be
resolved to a single known value.

## E.3 Assignments
Variables and constants are fully declared and assigned using IP-XACT parameters (see C.21 parameters). In other
words, the IP-XACT Expression Language itself does not support assignments and, therefore, does not
support any assignment operators.

### E.3.1 Single value assignment
To assign a single parameter with an identifier of baseAddress having a value of 'h100 in IP-XACT, use
the following format:
```xml
<ipxact:parameter type="longint" parameterId="baseAddress">
  <ipxact:name>baseAddress</ipxact:name>
  <ipxact:value>'h100</ipxact:value>
</ipxact:parameter>
```
which is equivalent to the following SystemVerilog assignment:
```verilog
longint baseAddress = 'h100;
```

### E.3.2 Parameter type
The value of a parameter is itself an expression and should be specified accordingly.  The type of the
parameter expression is defined by the type attribute. Possible values for this type attribute are bit, byte,
shortint, int, longint, shortreal, real, string.  These types correspond to their SystemVerilog counterparts as
described in [E.2](#e2).

The expression that is specified as the parameter’s value is implicitly cast to the parameter’s type. See C.7 complexBaseExpression
and C.21 parameters.

### E.3.3 Parameter signing
To change the signed-ness of a parameter, use the **sign** attribute (see C.6.2), whose value can be **signed** or
**unsigned**, e.g.,
```xml
<ipxact:parameter type="longint" parameterId="baseAddress" sign="signed">
  <ipxact:name>baseAddress</ipxact:name>
  <ipxact:value>'h100</ipxact:value>
</ipxact:parameter>
```
This property influences only the following types: **bit**, **byte**, **shortint**, **int**, and **longint**:
where the types **byte**, **shortint**, **int**, and **longint** are *signed* by default
and the type **bit** is *unsigned* by default.

The **sign** property does not influence **real**, **shortreal**, and **string** types; effectively, **sign** can be ignored for
these types.

### E.3.4 Vector assignment
To create a packed array bit-string, the IP-XACT Expression Language allows the specification of vector
information. Vector information can be specified only for parameters with a type of **bit**.

The following shows how to create a 8-bit packed array parameter with an identifier of *test* having the
value *8'hAB*:
```xml
<parameter type="bit" parameterId="test">
  <name>test</name>
  <vectors>
    <vector>
      <left>7</left><right>0</right>
    </vector>
  </vectors>
  <value>8'hAB</value>
</parameter>
```
which is the equivalent of
```verilog
bit [7:0] test = 8'hAB;
```

### E.3.5 Array assignment
To create an array for any type of parameter, the IP-XACT Expression Language allows the specification of
array information and multiple initial values.

The following shows how to create an array parameter with a type of **int** and an identifier of *test* having
the value *'{8'hAA,8'hAA,8'hAA,8'hAA,8'hAA,8'hAA,8'hAA}*:
```xml
<parameter type="int" parameterId="test">
  <name>test</name>
  <arrays>
    <array>
        <left>6</left><right>0</right>
    </array>
  </arrays>
  <value>'{8'hAA, 8'hAA, 8'hAA, 8'hAA, 8'hAA, 8'hAA, 8'hAA}</value>
</parameter>
```
This is the equivalent of
```verilog
longint test [0:6] = '{8'hAA,8'hAA,8'hAA,8'hAA,8'hAA,8'hAA,8'hAA};
```

The following shows how to create a packed bit array parameter with an identifier of *test* having the array
value *{'{8'h0,8'h1,8'h2,8'h3,8'h4,8'h5},'{8'h6,8'h7,8'h8,8'h9,8'hA,8'hB}}*:
```xml
<parameter type="bit" parameterId="test">
  <name>test</name>
  <vectors>
    <vector>
      <left>7</left><right>0</right>
    </vector>
  </vectors>
  <arrays>
    <array>
      <left>1</left><right>0</right>
      <left>5</left><right>0</right>
    </array>
  </arrays>
  <value>'{'{8'h0,8'h1,8'h2,8'h3,8'h4,8'h5}, '{8'h6,8'h7,8'h8,8'h9,8'hA,8'hB}}</value>
</parameter>
```
This is the equivalent of
```verilog
bit [0:7] test [0:1] [0:5] = '{'{8'h0,8'h1,8'h2,8'h3,8'h4,8'h5},'{8'h6,8'h7,8'h8,8'h9,8'hA,8'hB}};
```

### E.3.6 Identifiers
The **parameterId** (see see C.6.2), which is used as the identifier for the parameter by the expression language,
can be specified using all characters from the *XML schema NameChar definition*; however, the first
character of the **parameterId** shall not be a -, :, or ., a number, or any other character as specified by the
*XML schema NameStartChar definition*.

The **parameterId** shall be unique within the containing document.

### E.3.7 Identifier references
Parameters can be used in other expressions by referencing their identifier, the **parameterId**.
```xml
<ipxact:parameter parameterId="offset" type="int">
  <ipxact:name>offset</ipxact:name>
  <ipxact:value>'h100</ipxact:value>
</ipxact:parameter>
<ipxact:register>
  ...
  <ipxact:addressOffset>offset + 'h10</ipxact:addressOffset>
  ...
</ipxact:register>
```

Any parameter in the document with a **parameterId** can be referenced from an expression. However, view-
dependent parameters specified inside the instantiation sections cannot be referenced from outside the
instantiation that specifies the parameter.

The **parameterId** can be specified using the characters -, :, or .. However, to avoid confusion with the
expression operators, these characters cannot be directly specified when referencing the parameter from an
expression. In that case, these characters should be escaped first (see [E.3.7.1](#e731)).

Example
```
shiftreg_a
busa_index
error_condition
merge_ab
_bus3
```
Implementations may set a limit on the maximum length of identifiers, but the limit shall be at least 1024
characters. If an identifier exceeds the implementation-specific length limit, an error shall be reported.

(e731)=
#### E.3.7.1 Escaped identifier references
Escaped identifier references shall start with the backslash character (`\`) and end with white space (a space,
tab, or newline). They provide a means of including the characters that are part of the XML schema
NameChar definition, but are not allowed to be specified directly for an identifier.
The following extra characters can be used for an escaped character: `-`, `:`, and `..` Neither the leading
backslash character nor the terminating white space is considered to be part of the identifier reference.
Therefore, the escaped identifier reference `\cpu3` is treated the same as the non-escaped identifier
references `cpu3`.

Example
```
\busa:index
\:clock
\error-condition
\a.b
```

#### E.3.7.2 Keywords
Keywords are predefined non-escaped identifiers that are used to define the language constructs. All
keywords are defined in lowercase only. A keyword preceded by an escape character (see [E.3.7.1](#e731)) is not
interpreted as a keyword.

A subset of SystemVerilog keywords have been specified for IP-XACT. Since fewer keywords have been
specified in the IP-XACT Expression Language, the other SystemVerilog keywords need to be escaped (see
[E.3.7.1](#e731)) before processing these expressions using a SystemVerilog parser/processor.

The following keywords are reserved: **bit**, **byte**, **shortint**, **int**, **longint**, **shortreal**, **real**, **signed**, **unsigned**,
**inside**, and **with**.

## E.4 Operators
Table E.2 gives an overview of the SystemVerilog operators and how IP-XACT supports them (or not).

*Table E.2—SystemVerilog operators*
| Operator Token                        | Name                                          | Operand Data Types
|---------------------------------------|:----------------------------------------------|:--------------------------------------------
| `=`                                   | Binary assignment operator                    | <span style="color:red">Assignments are not supported</span>
| `+=` `-=` `/=` `*=`                   | Binary arithmetic assignment operators        | <span style="color:red">Assignments are not supported</span>
| `%=`                                  | Binary arithmetic modulus assignment operator | <span style="color:red">Assignments are not supported</span>
| `&=` `\|=` `^=`                       | Binary bit-wise assignment operators          | <span style="color:red">Assignments are not supported</span>
| `>>=` `<<=`                           | Binary logical shift assignment operators     | <span style="color:red">Assignments are not supported</span>
| `>>>=` `<<<=`                         | Binary arithmetic shift assignment operators  | <span style="color:red">Assignments are not supported</span>
| `?:`                                  | Conditional operator                          | integral`*`, real`†`, string
| `+` `-`                               | Unary arithmetic operators                    | integral`*`, real`†`
| !                                     | Unary logical negation operator               | integral`*`, real`†`
| `~` `&` `~&` `\|` `~\|` `^` `~^` `^~` | Unary logical reduction operators             | integral`*`
| `+` `-` `*` `/` `**`                  | Binary arithmetic operators                   | integral`*`, real`†`
| `%`                                   | Binary arithmetic modulus operator            | integral`*`
| `&` `\|` `^` `^~` `~^`                | Binary bit-wise operators                     | integral`*`
| `>>` `<<`                             | Binary logical shift operators                | integral`*`
| `>>>` `<<<`                           | Binary arithmetic shift operators             | integral`*`
| `&&` `\|\|` `->` `<->`                | Binary logical operators                      | integral`*`, real`†`
| `<` `<=` `>` `>=`                     | Binary relational operators                   | integral`*`, real`†`
| `===` `!==`                           | Binary case equality operators                | <span style="color:red">Unknown or high-impedance values are not supported</span>
| `==` `!=`                             | Binary logical equality operators             | integral`*`, real`†`, string
| `==?` `!=?`                           | Binary wildcard equality operators            | <span style="color:red">Unknown or high-impedance values are not supported</span>
| `++` `--`                             | Unary increment and decrement operators       | <span style="color:red">Assignments are not supported</span>
| `inside`                              | Binary set membership operator                | integral`*`, real`†`, string
| `dist`                                | Binary distribution operator                  | <span style="color:red">Randomization is not supported</span>
| `{}` `{{}}`                           | Concatenation and replication operators       | integral`*`, string
| `{<<{}}` `{>>{}}`                     | Stream operators                              | integral`*`

`*`integral = bit, byte, shortint, int, and longint
`†`real     = real and shortreal

All operators are supported except the following:
a) The assignment operators are not supported, since assignments are handled using IP-XACT constructs.
b) Operators that handle high-impedance and unknown equality are not supported. The IP-XACT
   Expression Language does not specify data-types that support high-impedance and unknown values;
   therefore, there is no need to support these operators.
c) The binary distribution operator is not supported because it is not possible to specify randomized values.

## E.5 Functions
The SystemVerilog Expression Language supports a set of functions; to make the expression language more
complete, the a set of functions is supported with additional functions specific to IP-XACT.

### E.5.1 Integer function
The integer function is shown in Table E.3.

*Table* E.3—Integer function
| Function    | Description
|-------------|:----------------------------------------------------------------------------------------------
| `$clog2(x)` | Returns the ceiling of the log base 2 of the argument (the log rounded up to an integer value)

### E.5.2 Real functions
The real functions are shown in Table E.4.

*Table E.4—Real functions*
| Function      | Description
|---------------|:----------------------------------------------------------------------------------------------
| `$ln(x)`      | Natural logarithm
| `$log10(x)`   | Decimal logarithm
| `$exp(x)`     | Exponential
| `$sqrt(x)`    | Square root
| `$pow(x,y)`   |  x**y
| `$floor(x)`   | Floor
| `$ceil(x)`    | Ceiling
| `$sin(x)`     | Sine
| `$cos(x)`     | Cosine
| `$tan(x)`     | Tangent
| `$asin(x)`    | Arc-sine
| `$acos(x)`    | Arc-cosine
| `$atan(x)`    | Arc-tangent
| `$atan2(y,x)` | Arc-tangent of y/x
| `$hypot(x,y)` | sqrt(x*x+y*y)
| `$sinh(x)`    | Hyperbolic sine
| `$cosh(x)`    | Hyperbolic cosine
| `$tanh(x)`    | Hyperbolic tangent
| `$asinh(x)`   | Arc-hyperbolic sine
| `$acosh(x)`   | Arc-hyperbolic cosine
| `$atanh(x)`   | Arc-hyperbolic tangent

### E.5.3 String function
The string function is shown in Table E.5.

*Table E.5—String function*
| Function      | Description
|---------------|:----------------------------------------------------------------------------------------------
| `$sformatf()` | Returns the IP-XACT string value specified by the initial format argument. Equivalent to the
|               | System Verilog $sformatf() function, but, it operates on IP-XACT string values.

#### E.5.3.1 $sformatf()
```bnf
"$sformatf" "(" format_string "," [ "," list_of_arguments ] ")"
```

Returns IP-XACT string, or unresolvedStringExpression.

This is derived from the existing formatted string function from IEEE Std 1800-2012 System
Verilog sections 21.3.3. The specification of format_string argument is derived from System
Verilog section 21.2.1.2. Unlike System Verilog the format_string argument must be an IP-XACT
expression with an IP-XACT string data type. The number of additional arguments must be at least
the number of format escape sequences in the format string argument which require a value or there
is an error. Additional arguments beyond the required number of arguments are formatted with
“%d”. The data type of the additional arguments must match the data type allowed for the escape
sequence or there is an error. For the argument type checking the argument type any the of
unresolved data types is considered to be the same as the corresponding original data types. If one
of the arguments other than the format_string is an unresolved data type then the return data type is
unresolvedStringExpression. Otherwise, the return value is an IP-XACT string data type. The
syntax of format string escape sequence is:
```bnf
escape_sequence       ::= basic_escape_sequence | real_escape_sequence
basic_escape_sequence ::= "%" [ width ] format
real_escape_sequence  ::= "%" [width] "." precision real_format
width                 ::= decimal_digit { decimal_digit }
precision             ::= decimal_digit { decimal_digit }
format                ::= basic_format | real_format
basic_format          ::= "B" | "C" | "D" | "H" | "O" | "S" | "X" | "b" | "c" | "d" | "h" | "o" | "s" | "x" | "%"
real_format           ::= "E" | "F" | "G" | "e" | "f" | "g"
```

If the escape sequence does not match the specified syntax the characters are placed into the result
unchanged.

Table E.6 shows a list of the IP-XACT format_string escape sequences:

The size of the resulting string is specified as in System Verilog section 21.2.1.3.

*Table E.6—Escape sequences*

<table border="1">
<tr><th>Escape Sequence</th><th>Description</th><th>IP-XACT Data Type Allowed</th></tr>
<tr>
  <td>
%h or %H<br/>
%x or %X
  </td>
  <td>
Hexadecimal format.<br/>
Lowercase format specifies lowercase result.<br/>
Uppercase format specifies uppercase result.
  </td>
  <td>
bit, byte, shortint, int, longint;<br/>
real and shortreal are first cast to longint
  </td>
</tr>
<tr>
  <td>%d or %D</td>
  <td>Decimal format.</td>
  <td>
bit, byte, shortint, int, longint;<br/>
real and shortreal are first cast to longint
  </td>
</tr>
<tr>
  <td>%o or %O</td>
  <td>Octal format.</td>
  <td>
bit, byte, shortint, int, longint;<br/>
real and shortreal are first cast to longint
  </td>
</tr>
<tr>
  <td>%b or %B</td>
  <td>Binary format.</td>
  <td>
bit, byte, shortint, int, longint;<br/>
real and shortreal are first cast to longint
  </td>
</tr>
<tr>
  <td>%c or %C</td>
  <td>ACSII character format.</td>
  <td>
bit, byte, shortint, int, longint;<br/>
real and shortreal are first cast to longint
  </td>
</tr>
<tr>
  <td>%s or %S</td>
  <td>String format.</td>
  <td>string</td>
</tr>
<tr>
  <td>%e or %E</td>
  <td>
Exponential format.<br/>
Lowercase format specifies<br/>
lowercase result.<br/>
Uppercase format specifies<br/>
uppercase result.
  </td>
  <td>
shortreal, real;<br/>
bit, byte, shortint, int, longint are first cast to real
  </td>
</tr>
<tr>
  <td>%f or %F</td>
  <td>Decimal format</td>
  <td>
shortreal, real;<br/>
bit, byte, shortint, int, longint are first cast to real
  </td>
</tr>
<tr>
  <td>%g or %G</td>
  <td>
Shorter of exponential or decimal.<br/>
Lowercase format specifies<br/>
lowercase result.<br/>
Uppercase format specifies<br/>
uppercase result.
  </td>
  <td>
shortreal, real;<br/>
bit, byte, shortint, int, longint are first cast to real
  </td>
</tr>
<tr>
  <td>%%</td>
  <td>The character %</td>
  <td>No argument</td>
</tr>
</table>

Example:
```xml
<command>$sformatf("run %c",byte unsigned'(A + 23))</command>
```

### E.5.4 IP-XACT specific functions
The IP-XACT specific functions are shown in Table E.7.

*Table E.7—IP-XACT specific functions*
| Function                                   | Description
|:-------------------------------------------|:----------------------------------------------------------------------------------------------
| `$ipxact_absdefport_value  ( identifier )` | Returns an IP-XACT unresolved bit expression value representing<br/>an abstraction definition port value.
| `$ipxact_field_value       ( identifier )` | Returns an IP-XACT unresolved bit expression value representing<br/>a field slice value.
| `$ipxact_index_value       ( identifier )` | Returns an IP-XACT unresolved unsigned longint expression value<br/>representing the array index from the array dimension that has<br/>the indexVar attribute value matching the argument.
| `$ipxact_mode_condition    ( identifier )` | Returns an IP-XACT unresolved bit expression value representing<br/>a mode condition value.
| `$ipxact_packetfield_value ( identifier )` | Returns an IP-XACT unresolved bit expression value representing<br/>a packet field value.
| `$ipxact_port_value        ( identifier )` | Returns an IP-XACT unresolved bit expression value representing<br/>a component port slice value.

#### E.5.4.1 $ipxact_absdefport_value()
```bnf
"$ipxact_absdefport_value" "(" identifier ")"
```
Returns IP-XACT unresolved bit expression.

Only allowed in the packetfield width value element.

The argument must be a reference to an abstraction definition port. It is an error if the abstraction
definition port is not found.

Example:
```xml
<ipxact:width>$ipxact_absdefport_value(portRef1) == 4'ha</ipxact:width>
```

#### E.5.4.2 $ipxact_field_value()
```bnf
"$ipxact_field_value" "(" field_slice_indentifier ")"
```
Returns IP-XACT unresolved bit expression.
Only allowed in the condition element value.
The argument must be a reference to a field slice. It is an error if the field slice is not found.

Example:
```xml
<ipxact:condition>$ipxact_field_value(fieldSliceRef1)==4'ha</ipxact:condition>
```

#### E.5.4.3 $ipxact_index_value()
```bnf
$ipxact_index_value ( identifier )
```
Returns IP-XACT unresolved unsigned longint expression.

Only allowed in the pathSegment element value.

The argument must match the indexVar attribute of a dim element. It is an error if the indexVar is
not found.

Example:
```xml
<ipxact:pathSegment>$sformatf("reg1[%0d]", $ipxact_index_value(N))</ipxact:pathSegment>
```

#### E.5.4.4 $ipxact_mode_condition()
```bnf
$ipxact_mode_condition ( mode_identifier )
```
Returns IP-XACT unresolved bit expression.

Only allowed in the condition element value.

The argument must be a reference to a mode. It is an error if the mode is not found.

Example:
```xml
<ipxact:condition>$ipxact_mode_condition(mode1)</ipxact:condition>
```

#### E.5.4.5 $ipxact_packetfield_value()
```bnf
$ipxact_packetfield_value ( identifier )
```
Returns IP-XACT unresolved bit expression.

Only allowed in the packetfield width element.

The argument must be a reference to a packetfield. It is an error if the packetfield is not found.

Example:
```xml
<ipxact:width>$ipxact_packetfield_value(packetfieldRef1)</ipxact:width>
```

#### E.5.4.6 $ipxact_port_value()
```bnf
$ipxact_port_value ( identifier )
```
Returns IP-XACT unresolved bit expression.

The argument must be a reference to a component port slice. It is an error if the port slice is not
found. It is also an error if the port referenced in the referenced port slice is not found as a result of
selecting a view in which that port does not exist. In other words, the conditions in which this
function is called shall only be resolved in views in which the port slice exists.

Example:
<ipxact:condition>$ipxact_port_value(portSlice) == 4'ha</ipxact:condition>

### E.5.5 IP-XACT specific escape sequences
The IP-XACT specific escape sequences are shown in Table E.8.

*Table E.8—IP-XACT escape sequences*
| Escape sequence                       | Description
|---------------------------------------|-------------------
| $ipxact_index_value( identifier )     | IP-XACT DE or generator resolvable string value representing the array
|                                       | index from the array dimension that has the indexVar attribute value
|                                       | matching the argument.
| $ipxact_parameter_value( identifier ) | IP-XACT DE or generator resolvable string value representing the
|                                       | parameter that has the parameterId attribute value matching the argument.

#### E.5.5.1 $ipxact_index_value()
```bnf
$ipxact_index_value ( identifier )
```
IP-XACT DE or generator resolvable string value.

Only allowed in displayName, description, and shortDescription values.

The argument must match the indexVar attribute of a dim element. It is an error if the indexVar is
not found.

Example:
```xml
<ipxact:displayName>reg_$ipxact_index_value(N)</ipxact:displayName>
```

#### E.5.5.2 $ipxact_parameter_value()
```bnf
$ipxact_parameter_value ( identifier )
```
IP-XACT DE or generator resolvable string value.

Only allowed in displayName, description, and shortDescription values.

The argument must match the parameterId attribute of a parameter element. It is an error if the
parameterId is not found.

Example:
```xml
<ipxact:displayName>component_$ipxact_parameter_value(P)</ipxact:displayName>
```

## E.6 Expression language formal syntax (BNF)
The formal syntax is described using Backus-Naur Form (BNF). The syntax of the expression language
source is derived from the starting symbol constant_expression (see E.6.3.3).
The following meta-syntax conventions used are used here:
  — Keywords and punctuation are in ~~red text~~ (sourounded by double quotes).
  — Syntactic categories are named in non-bold text.
  — A vertical bar ( | ) separates alternatives.
  — Square brackets ( [ ] ) enclose optional items.
  — Braces ( { } ) enclose items that can be repeated zero or more times.

### E.6.1 Declarations: declaration data types
```bnf
casting_type        ::= simple_type | constant_primary | signing
integer_type        ::= integer_vector_type | integer_atom_type
integer_atom_type   ::= "byte" | "shortint" | "int" | "longint"
integer_vector_type ::= "bit"
non_integer_type    ::= "shortreal" | "real"
signing             ::= "signed" | "unsigned"
simple_type         ::= integer_type | non_integer_type
```

### E.6.2 Behavioral statements: Case statements
#### E.6.2.1 Patterns
```bnf
assignment_pattern ::= "'{" constant_expression { "," constant_expression } "}"
                     | "'{" array_pattern_key ":" constant_expression { "," array_pattern_key ":" constant_expression } "}"
                     | "'{" constant_expression "{" constant_expression { "," constant_expression } "}" "}"
array_pattern_key                      ::= constant_expression | "default"
assignment_pattern_expression          ::= [ assignment_pattern_expression_type ] assignment_pattern
assignment_pattern_expression_type     ::= integer_atom_type
constant_assignment_pattern_expression ::= assignment_pattern_expression
```

#### E.6.2.2 Covergroup declarations
```bnf
open_range_list  ::= open_value_range { "," open_value_range }
open_value_range ::= value_range
```

### E.6.3 Expressions
#### E.6.3.1 Concatenations
```bnf
constant_concatenation          ::= "{" constant_expression { "," constant_expression } "}"
constant_multiple_concatenation ::= "{" constant_expression constant_concatenation "}"
constant_streaming_expression   ::= "{" stream_operator [ slice_size ] constant_stream_concatenation "}"
stream_operator                 ::= ">>" | "<<"
slice_size                      ::= simple_type | constant_expression
constant_stream_concatenation   ::= "{" constant_stream_expression { "," constant_stream_expression } "}"
constant_stream_expression      ::= constant_expression [ "with" "[" constant_array_range_expression "]" ]
constant_array_range_expression ::= constant_expression
                                  | constant_expression  ":" constant_expression
                                  | constant_expression "+:" constant_expression
                                  | constant_expression "-:" constant_expression
```

#### E.6.3.2 Subroutine calls
```bnf
math_function_call   ::= math_function_identifier    "(" list_of_arguments                      ")"
string_function_call ::= string_function_identifier  "(" list_of_arguments                      ")"
ipxact_function_call ::= "$ipxact_absdefport_value"  "(" abstraction_definition_port_identifier ")
                       | "$ipxact_field_value"       "(" field_slice_identifier                 ")
                       | "$ipxact_index_value"       "(" indexvar_identifier                    ")
                       | "$ipxact_mode_condition"    "(" mode_identifier                        ")
                       | "$ipxact_packetfield_value" "(" packetfield_identifier                 ")
                       | "$ipxact_port_value"        "(" port_slice_identifier                  ")
list_of_arguments    ::= [ constant_expression ] { "," [ constant_expression ] }
```

`$ipxact_absdefport_value` [^36]
`$ipxact_field_value` [^37]
`$ipxact_index_value` [^38]
`$ipxact_mode_condition` [^39]
`$ipxact_packetfield_value` [^40]
`$ipxact_port_value` [^41]

#### E.6.3.3 Expressions
```bnf
constant_expression        ::= constant_primary
                             | unary_operator constant_primary
                             | constant_expression binary_operator constant_expression
                             | constant_expression "?" constant_expression ":" constant_expression
                             | constant_inside_expression
constant_range_expression  ::= constant_expression  | constant_part_select_range
constant_part_select_range ::= constant_range       | constant_indexed_range
constant_range             ::= constant_expression  ":" constant_expression
constant_indexed_range     ::= constant_expression "+:" constant_expression
                             | constant_expression "-:" constant_expression
constant_inside_expression ::= constant_expression inside { open_range_list }
value_range                ::= constant_expression  | "[" constant_expression ":" constant_expression "]"
```

#### E.6.3.4 Primaries
```bnf
constant_primary    ::= primary_literal
                      | parameter_identifier constant_select
                      | constant_concatenation [ "[" constant_range_expression "]" ]
                      | constant_multiple_concatenation [ "[" constant_range_expression "]" ]
                      | "(" constant_expression ")"
                      | constant_streaming_expression
                      | constant_cast
                      | format_string_function_call
                      | math_function_call
                      | constant_assignment_pattern_expression
                      | condition_pattern
                      | segment_pattern
primary_literal     ::= number | unbased_unsized_literal | string_literal
constant_cast       ::= casting_type "’" "(" constant_expression ")"
constant_bit_select ::= { "[" constant_expression "]" }
constant_select     ::= constant_bit_select [ "[" constant_part_select_range "]" ]
```
condition_pattern[^42]
segment_pattern[^43]

#### E.6.3.5 Operators
```bnf
unary_operator  ::= "+" | "-"  | "!" | "~"  | "&" | "~&" | "|"  | "~|" | "^"  | "~^" | "^~"
binary_operator ::= "+" | "-"  | "*" | "/"  | "%" | "==" | "!=" | "&&" | "||" | "**"
                  | "<" | "<=" | ">" | ">=" | "&" | "|"  | "^"  | "^~" | "~^" | ">>" | "<<" | ">>>" | "<<<" | "->" | "<->"
```

#### E.6.3.6 Numbers
See A.8.7 in IEEE Std 1800-2012.

#### E.6.3.7 Strings
```bnf
string_literal ::= '"' { Any_ASCII_Characters } '"'
```

### E.6.4 General: Identifiers
```bnf
abstraction_definition_port_identifier ::= identifier
escaped_identifier                     ::= "\" {any_printable_ASCII_character_except_white_space} white_space
field_slice_identifier                 ::= identifier
identifier                             ::= simple_identifier | escaped_identifier
indexvar_identifier                    ::= :: identifier
integer_math_function_identifier       ::= "$clog2"
math_function_identifier               ::= integer_math_function_identifier | real_math_function_identifier
mode_identifier                        ::= identifier
packetfield_identifier                 ::= identifier
parameter_identifier                   ::= identifier
port_slice_identifier                  ::= identifier
simple_identifier                      ::= [ a-zA-Z_ ] { [ a-zA-Z0-9_$ ] }
real_math_function_identifier          ::= "$asin" | "$ln"    | "$acos" | "$log10" | "$atan" | "$exp" | "$atan2" | "$sqrt" | "$hypot" | "$pow"
                                         | "$sinh" | "$floor" | "$cosh" | "$ceil"  | "$tanh" | "$sin" | "$asinh" | "$cos"  | "$acosh" | "$tan" | "$atanh"
string_function_identifier             ::= "$sformatf"
```

## E.7 SystemVerilog conversion steps
To be able to verify the IP-XACT Expression Language using a SystemVerilog parser or tool, the IP-XACT
Expression Language needs to be converted to the SystemVerilog Expression language.
This can be achieved using the following (simple) steps.

### E.7.1 Convert parameter
a) Convert the vector(s) left and right information to SystemVerilog (packed) array indexes.
b) Normalize the characters in the name of the parameter to valid SystemVerilog characters by
replacing all -, :, and . characters and non US-ASCII characters with a predefined character (or set
of characters), e.g., use an underscore (_) instead.
c) Escape all identifiers that could be interpreted as SystemVerilog keywords.
d) Convert the array(s) left and right information to SystemVerilog (unpacked) array indexes.
e) Convert the value and array values (see E.7.2).

### E.7.2 Convert expression
Convert all identifiers by normalizing the characters: use the same mechanism as specified by steps c) and d) in E.7.1.

## E.8 SystemVerilog reference
The following subclauses of IEEE Std 1800-2012 have been used to determine the IP-XACT Expression
Language functionality:

**6 – Data Types:** the following subclauses should be considered:
**— 6.1 - General:** only the parts discussing the type operators, compatibility, and casting.
**— 6.2 - Data types and data objects:** should be considered, apart from any distinctions noted in [E.2](#e2).
**— 6.3 - Value Set:** only the subclause about the logical 0 and 1 values (6.3.1); the subclauses about
strength should not be taken into consideration.
**— 6.4 - Singular and aggregate types, 6.5 - Nets and variables, 6.6 - Net types, 6.7 - Net declara-
tions, and 6.8 - Variable declarations:** should not be considered.
**— 6.9 - Vector declarations:** only bit vectors should be considered. Also the declaration of vectors is
handled by an IP-XACT construct and can be ignored.
**— 6.10 - Implicit declarations:** can be ignored because identifiers can be created only using the IP-
XACT parameter mechanism
**— 6.11 - Integer data types:** only **byte**, **shortint**, **int**, **longint**, and **bit** should be considered; these are
2-state data-types; therefore, all 4-state data types can be ignored.
**— 6.12 - Real, shortreal and realtime data types:** only the real data-type should be considered.
**— 6.13 - Void data type, 6.14 - Chandle data type,** and **6.15 - Class:** are not supported by the IP-
XACT Expression Language and should not be considered.
**— 6.16 - String data type:** the IP-XACT string data-type functionality has been simplified consider-
ably; only the equality, inequality, concatenation and replication operators should be considered.
**— 6.17 - Event data type, 6.18 - User-defined types, 6.19 - Enumerations,** and **6.20 - Constants:**
cannot be specified using the IP-XACT expression language and should not be considered.
**— 6.21 - Scope and lifetime:** is handled by the IP-XACT XML Format, which is outside of the IP-
XACT Expression Language.
**— 6.22 - Type compatibility:** only the parts that discuss the **byte**, **shortint**, **int**, **longint**, **bit**, **shortreal**,
and **real** data-types should be considered.
**— 6.23 - Type operator:** the type operator is not supported and should not be considered.
**— 6.24 - Casting:** only the parts that discuss the **byte**, **shortint**, **int**, **longint**, **bit**, **short**real****, and real
data-types should be considered.
**— 6.25 - Parameterized data types:** should not be considered.

**7 – Aggregate data types:** only the parts about packed arrays and unpacked arrays should be considered.
**— 7.1 - General:** only the part on packed and unpacked arrays should be considered.
**— 7.2 - Structures** **and 7.3 – Unions:** are not supported and should not be considered.
**— 7.4 - Packed and unpacked arrays:** should be fully considered.
**— 7.5 - Dynamic arrays:** are not supported and should not be considered.
**— 7.6 - Array assignments:** are handled by the IP-XACT XML Format; however, the format of the
assignment should still be considered.
**— 7.7 - Arrays as arguments to subroutines:** subroutines are not supported and should not be consid-
ered.
**— 7.8 - Associative arrays:** are not supported and should not be considered.
**— 7.9 - Associative array methods:** are not supported and should not be considered.
**— 7.10 - Queues:** are not supported and should not be considered.
**— 7.11 - Array querying functions:** and **7.12 - Array manipulation methods:** are not supported and
should not be considered.

**10 – Assignment statements:** only 1**0.9 - Assignment patterns** should be considered, in particular **10.9.1**,
which clarifies the array assignment patterns.

**11 – Operators and expressions:** the following subclauses should be considered:
**— 11.1 - General:** should be considered, apart from the operators and expressions discussed in E.4.
**— 11.2 - Overview:** where for the operand subclause only, constant literal numbers, string literals,
packed array, and unpacked arrays should be considered.
**— 11.3 - Operators:** only the operators identified for the IP-XACT Expression Language should be
considered and only on the data-types allowed. The assignment within an expression section can be
ignored.
**— 11.4 - Operator descriptions:** only Arithmetic operators, Relational operators, Equality operators (x
and z excluded), Logical operators, Bitwise operators, Reduction operators, Shift operators, Condi-
tional operators, Concatenation, Set membership, and streaming operators should be considered.
**— 11.5 - Operands:** should be considered.
**— 11.6 - Expression bit lengths:** should be considered for the **byte**, **shortint**, **int**, **longint**, **bit**, **short-
real**, and **real** values.
**— 11.7 - Signed expressions:** the $signed and $unsigned system functions are not supported and
should be ignored.
**— 11.8 - Expression evaluation rules:** should be considered, however the subclauses about evaluating
an assignment and handling of X and Z values can be ignored.
**— 11.9 - Tagged union expressions and member access:** unions are not supported and can be ignored.
**— 11.10 - String literal expressions:** are not supported and can be ignored.
**— 11.11 - Operator overloading:** is not supported and can be ignored.
**— 11.12 - Minimum, typical, and maximum delay expressions:** delay expressions are not supported
and can be ignored.
**— 11.13 - Let construct:** this construct is not supported and can be ignored.

**20 - Utility system tasks and system functions:** only **20.8 - Math functions** should be considered.


[^36]: The $ipxact_absdefport_value() function only allowed in the packetfield width element value.
[^37]: The $ipxact_field_value() function only allowed in the condition element value.
[^38]: The $ipxact_index_value() function only allowed in the pathSegment element value.
[^39]: The $ipxact_mode_condition() function only allowed in the condition element value.
[^40]: The $ipxact_packetfield_value() function only allowed in the packetfield width element value.
[^41]: The $ipxact_port_value() function only allowed in the condition element value.
[^42]: Alternative only valid on unresolve type of kind mode/condition expression.
[^43]: Alternative only valid on unresolve type of kind segment_path expression.
