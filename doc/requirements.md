# Capping analyser tool requirements

Objective: The tool shall test and display the successful or unsuccessful capping operations applied to HPC systems, under varying load conditions.

## Requirements

- Put system under varying load and perform capping operations
- Measure the consumed power via BMC
- Record the capping level and capping state (active/inactive)
- Measure the consumed power via RAPL
- Support for both IMPI and Redfish BMCs
- Write data to database
- Provide graphing/analysis tool
- Report system information for the server under test (Server type, CPU type, CPU count, ...)
- Capping operations to include:
  - Activate after setting level
  - Set level after activate
  - Cap up and down
  - Activate and deactivate cap
- Data collected incrementally during the run
- Log the return code from BMC capping operations to database
