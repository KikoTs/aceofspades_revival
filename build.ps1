param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$BuildArgs
)

python tools/build_release.py @BuildArgs
