param(
    [ValidateSet("api", "postgres", "all")]
    [string]$Service = "all",
    [int]$Tail = 100
)

$ErrorActionPreference = "Stop"

if ($Service -eq "all") {
    docker compose logs --tail $Tail
}
else {
    docker compose logs --tail $Tail $Service
}
