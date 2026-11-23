from typing import Any, Union

# normally one of the keys in the PUBLIC_RECORDS map,
# but might also be prefixed with , all_, gather_, etc.
TargetName = str

# any extra arguments needed to identify a record (guardian_id etc)
# has to be frozen (hashable) to go in results below
TargetArgs = tuple[tuple[str, Any]]

# error message
Error = str

# successfully verified public record
Success = Any

# main state of the verify program
ResultsCache = dict[
    TargetName,
    dict[TargetArgs,
         Union[Error, Success]
    ]
]

# summary of just the failed results
Errors = dict[
    TargetName,
    dict[TargetArgs, Error]
]

Successes = dict[
    TargetName,
    dict # TODO variant of Dict[TargetArgs, Success] that can go into a JSON
]

# flat summary of whether each top-level node was verified
# (not including the ones that are mapped over lots of files)
VerifiedBools = dict[TargetName, bool]

class DependencyError(Exception):
    "Make a target fail when one or more of its deps does"
