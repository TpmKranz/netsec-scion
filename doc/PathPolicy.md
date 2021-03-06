# Path Policy Language Design

The path policy language will be used by the path server, SCIOND and the beacon server for different
but overlapping purposes.

## Hop Predicate (HP)

A hop predicate is of the form **ISD-AS#IF,IF**. The first **IF** means the inbound interface
(the interface where packet enters the AS) and the second **IF** means the outbound interface
(the interface where packet leaves the AS).

_0_ can be used as a wildcard for **ISD**, **AS** and both **IF** elements indepedently.

It is possible to specify only a single interface for a hop (**ISD-AS#IF**). In that case the packet
must pass through the specified interface either when it's entering or leaving the AS. This syntax
is handy for the first and last hops of the path where the packet goes only through a single
interface anyway.

If the tail elements in a HP are 0, they can be omitted. See the following examples for details.

Examples:

- Match ISD _1_: `1` or `1-0` or `1-0#0` or `1-0#0,0`
- Match AS _1-ff00:0:133_: `1-ff00:0:133` or `1-ff00:0:133#0` or `1-ff00:0:133#0,0`
- Match inbound IF _2_ of AS _1-ff00:0:133_: `1-ff00:0:133#2,0`
- Match outbound IF _2_ of AS _1-ff00:0:133_: `1-ff00:0:133#0,2`
- Match inbound or outbound IF _2_ of AS _1-ff00:0:133_: `1-ff00:0:133#2`

## Operators

The path policy language has the following operators:

ACL:

- `+` (allow predicate)
- `-` (deny predicate)

Sequence:

- `?` (the preceding HP may appear at most once)
- `+` (the preceding **ISD-level** HP must appear at least once)
- `*` (the preceding **ISD-level** HP may appear zero or more times)
- `|` (logical OR)

Planned:

- `!` (logical NOT)
- `&` (logical AND)

## Policy

A policy is defined by a policy object. It can have the following attributes:

- [`extends`](#Extends) (list of extended policies)
- [`acl`](#ACL) (list of HPs, preceded by `+` or `-`)
- [`sequence`](#Sequence) (space separated list of HPs, may contain operators)
- [`options`](#Options) (list of option policies)
    - `weight` (importance level, only valid under `options`)

Planned:

- `bw` (bandwidth)
- `lat` (latency)
- `cost`
- `mtu`
- `exp` (expiration time)
- `frh` (freshness)
- `hops` (number of hops)
- `type` (defines where the policy should apply)
- `peer` (peer segments)
- `shct` (shortcut segments)

## Specification

### ACL

The ACL can be used to deny (blacklist) or allow (whitelist) ISDs, ASes and IFs. A deny entry is of
the following form `- ISD-AS#IF`, where the second part is a [HP](#HP). If a deny entry matches any
hop on a path, the path is not allowed.

An allow entry uses `+` with a HP, ie. `+ ISD-AS#IF`. For a path to be allowed, every hop of the
path must be allowed by the ACL. When using allow and deny entries in the same ACL, the first
matched entry wins. Thus, if an interface is denied by the first entry but allowed by the second
entry it is still denied.

Every ACL must end with a blanket accept or deny (i.e. `+` or `-`, or equivalent such as `+ 0-0#0`).
If a policy has no acl attribute (and doesn't inherit one from any policy it extends), then by
default everything is whitelisted.

The following is an example for allowing all interfaces in ASes _1-ff00:0:133_ and _1-ff00:0:120_,
but denying all other ASes in ISD _1_. The last entry makes sure that any other ISD is allowed.

```yaml
- acl_policy_example:
    acl:
    - '+ 1-ff00:0:133'
    - '+ 1-ff00:0:120'
    - '- 1'
    - '+'
```

### Sequence

The sequence is a string of space separated HPs. The [operators](#Operators) can be used for
advanced interface sequences.

The following example specifies a path from any interface in AS _1-ff00:0:133_ to two subsequent
interfaces in AS _1-ff00:0:120_ (entering on interface _2_ and exiting on interface _1_), then there
are two wildcards that each match any AS. The path must end with any interface in AS _1-ff00:0:110_.

```yaml
- sequence_example_2:
    sequence: "1-ff00:0:133#0 1-ff00:0:120#2,1 0 0 1-ff00:0:110#0"
```

Any path that is matched by the above policy must traverse three transit ASes. In many cases the
number of ASes or hops is not known. With the regex-style it is possible to express such sequences.

The following example specifies a path from interface _1-ff00:0:133#1_ through multiple ASes in ISD
_1_, that may (but does not need to) traverse AS _2-ff00:0:1_ and then reaches its destination on
_2-ff00:0:233#1_.

```yaml
- sequence_more_complex:
    sequence: "1-ff00:0:133#1 1+ 2-ff00:0:1? 2-ff00:0:233#1"
```

### Extends

Path policies can be composed by extending other policies. The `extends` attribute requires a list
of named policies. If an attribute exists in multiple policies in that list, the last occurence has
precedence. Also, an attribute specified at top level (the policy that has the `extends` attribute)
always has precedence over attributes of an extended policy.

The following example uses three sub-policies to create the top-level policy. As `sub_pol_1` and
`sub_pol_3` both define an ACL but `sub_pol_3` has precedence, the ACL of `sub_pol_1` is discarded.

```yaml
- extends_example:
    extends:
    - sub_pol_1
    - sub_pol_2
    - sub_pol_3

- sub_pol_1:
    acl:
    - "- 1-ff00:0:133#0"
    - "+"

- sub_pol_2:
    sequence: "0+ 1-ff00:0:110#0 1-ff00:0:110#0 0+"

- sub_pol_3:
    acl:
    - "- 1-ff00:0:131#0"
    - "- 1-ff00:0:132#0"
    - "- 1-ff00:0:133#0"
    - "+"
    mtu: ">=1000"
```

### Options

The `options` attribute requires a list of anonymous policies. Each policy may have `weight` as an
attribute to specify its importance and may have all other attributes of a policy. Options are
evaluated in the order of their weight. The paths of the policy with the highest weight are used, if
the heighest-weight policy does not match any paths, the next policy is evaluated. When multiple
policies have the same weight, all of their paths are returned. The default for a weight (when it is
omitted) is 0. All paths returned by an option must also match every condition of the top-level
policy (the top-level policy is ANDed to every option).

The following example has three options, the first denies ISD 1. If that doesn't match any paths,
the second option which denies hops in multiple ASes is used. If that again does not match, the
third option which denies only hops in AS _1-ff00:0:133_, is used.

```yaml
- policy_with_options:
    options:
      - weight: 3
        extends: option_3
      - weight: 2
        acl:
        - "- 1-ff00:0:130#0"
        - "- 1-ff00:0:131#0"
        - "- 1-ff00:0:132#0"
        - "+"
      - extends: option_1

- option_3:
    acl:
    - "- 1"
    - "+"
- option_1:
    acl:
    - "- 1-ff00:0:133#0"
    - "+"
```

## Path policies in path lookup

### Requirements

1. The path lookup path policy languages has to be at least as expressive as what we offer to
   clients. Otherwise we will need to have a middle man which requests all the required segments
   until a request can be fulfilled.
1. The path lookup path policy can only contain static properties of a path. Static are the acl and
   sequence parts of the policy and everything that does not contain information that can
   dynamically change, like latency (note that min latency of a link is probably a helpful static
   property).
1. The path lookup result caching should, if possible, not be affected by this change.

### Path lookup flow

1. Client sends request towards sciond with a policy in the request.
1. Sciond checks if it has recently done a request with the same policy for the destination
    1. Recent request done: build path from cache and filter with policy, return result to client.
    1. Cached segments not present: continue with steps below.
1. Sciond sends request with policy to local PS
1. PS checks if it has cached segments for the destination
    1. Cached segments present: filter segments with policy, return result to client.
    1. Cached segments not present: continue with steps below.
1. PS sends request to relevant core PS (according to current rules) with a flag indicating that all
   paths should be returned.
1. PS stores reply in its DB and filters segments with policy and returns it to sciond.
1. Sciond builds paths and filters them with policy and return them to the client.

Note that for the request caching in sciond we need to remember which policies were used in a
request. For that we use a time & space limited cache. It caches a result for a destination and a
certain policy up to x seconds. But it also starts to drop items once there are more than y requests
with different policies. To differentiate policies the hash of the serialized policy is used, so two
policies with the same effect but different representation will count separately.

### API changes

We have to change the sciond `PathReq` and the PS `SegReq` to include at policy field. The field
should encapsulate the `pathpol.PolicyMap` go type. Preferably a capnproto type would be used to
model it and if that is not possible we should serialize the type to JSON and send it as text field.

### Possible implementation shortcuts

It would be possible for the local PS to just return all the segments without filtering since sciond
has to do filtering anyway. Since the API of the PS will already accept policies we can just forward
the policy from sciond to the PS and the PS can either filter segments or just return all segments
without filtering.
