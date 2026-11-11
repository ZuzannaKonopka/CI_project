# Metric validation (error injection into reference trees)

| Error | Cases | sound | activity_f1 | footprint_sim | trace_p | trace_r | trace_f1 |
|---|---|---|---|---|---|---|---|
| none | 20 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| paraphrase_labels | 20 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| and_to_seq | 8 | 1.00 | 1.00 | 0.84 | 1.00 | 0.53 | 0.67 |
| or_to_xor | 6 | 1.00 | 1.00 | 0.85 | 1.00 | 0.19 | 0.32 |
| or_to_and | 6 | 1.00 | 1.00 | 1.00 | 1.00 | 0.39 | 0.56 |
| xor_to_and | 10 | 1.00 | 1.00 | 0.87 | 0.00 | 0.00 | 0.00 |
| drop_loop | 7 | 1.00 | 0.88 | 0.90 | 1.00 | 0.25 | 0.39 |
| drop_activity | 19 | 1.00 | 0.91 | 0.85 | 0.02 | 0.02 | 0.02 |
| swap_sequence | 14 | 1.00 | 1.00 | 0.72 | 0.16 | 0.16 | 0.16 |
