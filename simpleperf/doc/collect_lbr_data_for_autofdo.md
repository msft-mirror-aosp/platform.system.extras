# Collect LBR (x86 Architectures) data for AutoFDO

[TOC]

## Introduction

Intel's Performance Monitoring Unit (PMU) is a hardware feature built into their processors to measure various
performance parameters. These parameters include instruction cycles, cache hits, cache misses, branch misses,
and more1. The PMU helps in understanding how effectively code uses hardware resources and provides insights
for optimization.The Last Branch Record (LBR) is indeed a part of Intel's Performance Monitoring Unit (PMU).
The PMU includes various performance monitoring features, and LBR is one of them.

The Last Branch Record (LBR) is an advanced CPU feature designed to meticulously log the source and destination
addresses of recently executed branch instructions. This capability serves as a vital tool for performance
monitoring and debugging, allowing developers to track the intricate control flow of their programs. By analyzing
the data captured through LBR, we can gain valuable insights into how applications navigate through their execution
paths and pinpoint the areas where the program spends most of its time-often referred to as "hot paths."

Branch Statistics:
One of the remarkable applications of LBR is its ability to gather comprehensive branch statistics in C++ programs.
This data can be pivotal in understanding the behavior of conditional decisions in the code.

Virtual Calls:
LBR proves particularly useful for analyzing the outcomes of indirect branches and virtual calls, key components in
object-oriented programming that can significantly influence performance.

LBR entries are rich with information, typically consisting of `FROM_IP` and `TO_IP`, which denote the source and
destination addresses of the branching instructions. This detailed logging offers a clear view of the program's
execution flow.

Model Specific Registers (MSRs):
The configuration of LBR relies on Model Specific Registers (MSRs) specific to Intel CPUs. These registers play
a crucial role in enabling and managing LBR functionalities.

IA32_DEBUGCTL: To initiate LBR recording, one must set bit 0 of the IA32_DEBUGCTL register to 1, effectively
activating this powerful feature.

MSR_LASTBRANCH_x_FROM_IP:
This particular register is responsible for storing the originating addresses of the most recent branch instructions,
preserving a trail of execution paths.

MSR_LASTBRANCH_x_TO_IP: Conversely, this register captures the destination addresses of those most recent branches,
creating a comprehensive map of transitions within the program.

Clearing LBRs: A noteworthy aspect of LBR is that it gets cleared when the CPU enters certain low-power sleep states
deeper than C2. To maintain the integrity of the recorded data, it may be necessary to keep the CPU in an awake state.

Stopping LBR: Ceasing LBR recording can present challenges and might require invoking performance monitoring
interrupts (PMIs), introducing additional complexity to the management of this feature.

Advantages:
Overhead: One of the standout benefits of LBR is its minimal overhead; it provides nearly zero performance degradation
compared to traditional software-based branch recording methods, making it an efficient choice in performance-sensitive applications.

Accuracy: Although manual code instrumentation might yield slightly better precision in certain scenarios, this advantage
comes at the significant cost of increased runtime performance overhead, making LBR a more appealing alternative in many cases.

Scenarios: The utility of LBR shines particularly in situations where the source code is not readily accessible or when
the software builds process remains shrouded in mystery. In such cases, LBR becomes an invaluable ally in uncovering insights
into program behavior, allowing developers and analysts to make informed decisions based on the recorded execution paths.


Simpleperf supports collecting LBR data and converting it to input files for AutoFDO, which can then be used for
Feedback Directed Optimization during compilation.

## Examples

Below are examples collecting LBR data for AutoFDO. It has two steps: first recording LBR data,second converting LBR data to
AutoFDO input files.

Record LBR data:

# preparation: we need to be root the device to record LBR data
$ adb root
$ adb shell
brya:/ \# cd data/local/tmp
brya:/data/local/tmp \#

# Do a system wide collection, it writes output to perf.data.
# If only want LBR data for kernel, use `-e BR_INST_RETIRED.NEAR_TAKEN:k`.
# If only want LBR data for userspace, use `-e BR_INST_RETIRED.NEAR_TAKEN:u`.
# If want LBR data for system wide collection, use `-e BR_INST_RETIRED.NEAR_TAKEN -a`.

brya:/data/local/tmp \# simpleperf record -b -e BR_INST_RETIRED.NEAR_TAKEN:u -c 100003

simpleperf record:
The simpleperf record command is used to profile processes and store the profiling data in a file (usually�perf.data).

-b:
This option enables branch recording. It uses the Last Branch Record (LBR) feature of the CPU to capture the
most recent branches taken by the processor. This is useful for understanding the control flow of a program.

-a:
This option tells perf to record system-wide. It collects performance data from all CPUs, not just the one
where the command is run. This is useful for capturing a comprehensive view of system performance.

-e:
This option specifies the event (BR_INST_RETIRED.NEAR_TAKEN in this case) to record.

# To reduce file size and time converting to AutoFDO input files, we recommend converting LBR data into an intermediate branch-list format.

brya:/data/local/tmp \# simpleperf inject -i perf.data --output branch-list -o branch_list.data
```
Converting LBR data to AutoFDO input files needs to read binaries.
So for userspace and kernel libraries, it needs to be converted on host, with vmlinux and kernel modules available.

Convert LBR data for userspace libraries:

```sh
# Injecting LBR data on device. It writes output to perf_inject.data.
# perf_inject.data is a text file, containing branch counts for each library.
```

Convert LBR data for Userspace & kernel:

```sh
# pull LBR data to host.
host $ adb pull /data/local/tmp/branch_list.data
# download vmlinux and kernel modules to <binary_dir>
# host simpleperf is in <aosp-top>/aosp/out/host/linux-x86/bin/simpleperf,
# or you can build simpleperf by `mmma system/extras/simpleperf`.
host $ simpleperf inject --symdir <binary_dir> -i branch_list.data
simpleperf inject -i branch_list.data --binary <userspacelibrary> --symdir <symboldir> -o perf_inject.data

```
The generated perf_inject.data may contain branch info for multiple binaries. But AutoFDO only
accepts one at a time. So we need to split perf_inject.data.
The format of perf_inject.data is below:

```perf_inject.data format

executed range with count info for binary1
branch with count info for binary1
// name for binary1

executed range with count info for binary2
branch with count info for binary2
// name for binary2

...
```

We need to split perf_inject.data, and make sure one file only contains info for one binary.

Then we can use [AutoFDO](https://github.com/google/autofdo) to create profile. Follow README.md
in AutoFDO to build create_llvm_prof, then use `create_llvm_prof` to create profiles for clang.

```sh
# perf_inject_binary1.data is split from perf_inject.data, and only contains branch info for binary1.
host $ create_llvm_prof -profile perf_inject_binary1.data -profiler text -binary path_of_binary1 -out a.prof -format extbinary

# perf_inject_kernel.data is split from perf_inject.data, and only contains branch info for [kernel.kallsyms].
host $ create_llvm_prof -profile perf_inject_kernel.data -profiler text -binary vmlinux -out a.prof -format extbinary
```

Then we can use a.prof for AFDO during compilation, via `-fprofile-sample-use=a.prof`.
[Here](https://clang.llvm.org/docs/UsersManual.html#using-sampling-profilers) are more details.

