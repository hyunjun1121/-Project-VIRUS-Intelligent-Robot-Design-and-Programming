---
source_url: https://huggingface.co/datasets/Eason666/DrafterBench
converted_at: 2025-08-21 13:06:32
---

# Dataset Card for DrafterBench

## Dataset Description

DrafterBench is a large-scale toolkit focused on evaluating the proficiency of Large Language Models (LLMs) in automating Civil Engineering tasks.
This dataset hosts a task suite summarized across 20 real-world projects, encompassing a total of 1920 tasks.
It replicates the complexity of real-world engineering tasks and provides a technical platform to test the four key capabilities of LLMs:

- **Structured data understanding**
- **Function execution**
- **Instruction following**
- **Critical reasoning**

***Homepage***:[Project page](https://github.com/Eason-Li-AIS/DrafterBench/tree/DrafterBench)  
***Paper***:[DrafterBench: Benchmarking Large Language Models for Tasks Automation in Civil Engineering](https://arxiv.org/abs/2507.11527)

## Task Summary

The DrafterBench is constructed on tasks over three object elements, four operations, and six complexity controllers.

| Elements | Operations | Complexity Controllers | Capacities Investigated by Various Complexity |
| --- | --- | --- | --- |
| Text | Add new content | Language style (Structured/Unstructured) | Structured data understanding |
| Table | Revise content | Task categories | Function execution |
| Vector entity | Change position | Objects per instruction (Single/Multiple) | Instruction following |
|  | Update format | Operations per object (Single/Multiple) | Instruction following |
|  |  | Instruction completeness (Complete/Incomplete) | Critical reasoning |
|  |  | Detail ambiguity (Precise/Vague) | Critical reasoning |

## Quick start

Please refer to the quick start section on our [Project page](https://github.com/Eason-Li-AIS/DrafterBench/tree/DrafterBench)

## LeaderBoard

| Metric | OpenAI o1 | gpt-4o-2024-08-06 | Claude3.5-sonnet | Deepseek-v3-685B | Qwen2.5-72B-Instruct | Llama3-70B-Instruct |
| --- | --- | --- | --- | --- | --- | --- |
| Structured language | **81.58** | 75.14 | 74.34 | 75.66 | 74.57 | 68.96 |
| Unstructured language | **82.26** | 73.84 | 78.20 | 75.04 | 72.16 | 67.92 |
| Precise detail | **89.82** | 79.41 | 81.15 | 78.79 | 75.12 | 71.36 |
| Vague detail | **74.02** | 69.57 | 71.39 | 71.91 | 71.55 | 65.37 |
| Complete instruction | 80.98 | 81.70 | 83.72 | 85.59 | **87.58** | 83.10 |
| Incomplete instruction (Error) | **82.85** | 67.27 | 68.83 | 65.10 | 59.16 | 53.78 |
| Single object | **83.23** | 73.75 | 74.97 | 74.94 | 74.18 | 67.22 |
| Multiple objects | **80.60** | 75.23 | 77.57 | 75.76 | 72.56 | 69.66 |
| Single operation | **82.45** | 75.84 | 76.62 | 77.17 | 75.88 | 71.02 |
| Multiple operations | **80.84** | 71.79 | 75.56 | 71.70 | 68.36 | 63.27 |
| Average of 12 tasks | **81.92** | 74.49 | 76.27 | 76.05 | 73.37 | 68.44 |
| Comprehensive score | **79.90** | 71.76 | 73.79 | 73.09 | 70.52 | 64.95 |

Note: We have recently upgraded DrafterBench to be more challenging. Although the trend of models' ability is very consistent with the above leaderboard, some models may score lower than the records.

## Citation

If you use this dataset in your research, please consider citing our paper:

```
@article{drafterbench,
  title={DrafterBenchmark: Benchmarking Large Language Models for Tasks Automation in Civil Engineering},
  author={Yinsheng Li, Zhen Dong, Yi Shao.},
  year={2025},
  url={https://arxiv.org/abs/2507.11527},
}
```

Downloads last month
:   947

Use this dataset

Size of downloaded dataset files:

3.7 MB[Size of the auto-converted Parquet files:

445 kB](/datasets/Eason666/DrafterBench/tree/refs%2Fconvert%2Fparquet/)Number of rows:

1,920

System theme

