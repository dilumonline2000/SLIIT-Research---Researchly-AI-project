---
tags:
- sentence-transformers
- sentence-similarity
- feature-extraction
- generated_from_trainer
- dataset_size:210
- loss:ContrastiveLoss
base_model: sentence-transformers/all-MiniLM-L6-v2
widget:
- source_sentence: I am working on explainable AI and model interpretability
  sentences:
  - 'Supervisor: Doctor Prasanna Sumathipala. Department: DS. Research Cluster: CEAI.
    Research Interests: Explainable AI; Text Analytics; Evolutionary Computing; Neuro
    Computing. Keywords: explainable AI text analytics evolutionary computing neural
    networks'
  - 'Supervisor: Mr/Ms Sanjeevi Chandrasiri. Department: IT. Research Cluster: CEAI.
    Research Interests: Medical Image Processing; AI; Neural Networks; NLP; E-Learning.
    Keywords: medical image processing AI neural networks NLP e-learning'
  - 'Supervisor: Mr/Ms Aruna Ishara Gamage. Department: IM. Research Cluster: MR.
    Research Interests: Interactive Multimedia; Entertainment Content; Computer Animation;
    VFX; Image Processing; Mixed Reality; HCI; Geo-Informatics; Digital Photography;
    Machine Learning. Keywords: multimedia animation VFX mixed reality image processing
    HCI'
- source_sentence: I am developing a real-time object detection system using YOLO
  sentences:
  - 'Supervisor: Mr/Ms Lokesha Weerasinghe. Department: IT. Research Cluster: CEAI.
    Research Interests: Computer Vision; Image Processing; Machine Learning. Keywords:
    computer vision image processing machine learning'
  - 'Supervisor: Doctor Lakmini Abeywardhana. Department: DS. Research Cluster: CEAI.
    Research Interests: Deep Learning; Computer Vision; Computational Biology; Analysis
    and Modeling. Keywords: deep learning computer vision computational biology image
    analysis'
  - 'Supervisor: Doctor Nathali Silva. Department: IT. Research Cluster: CEAI. Research
    Interests: IoT; Smart Homes; Data Analytics; Deep Learning. Keywords: IoT smart
    homes data analytics deep learning'
- source_sentence: My investigate is about software complexity metrics and refactoring
  sentences:
  - 'Supervisor: Mr/Ms Uthpala Samarakoon. Department: IT. Research Cluster: SST.
    Research Interests: E-Learning; HCI; Social Science; IT Education; Knowledge Management.
    Keywords: e-learning HCI social science knowledge management education'
  - 'Supervisor: Professor Dilshan De Silva. Department: SE. Research Cluster: SST.
    Research Interests: Software Metrics; Software Complexity; Machine Translation;
    AR; VR; Mobile Development; Computer Linguistics. Keywords: software metrics AR
    VR mobile development machine translation'
  - 'Supervisor: Doctor Harinda Fernando. Department: CS. Research Cluster: IAS,CEAI.
    Research Interests: Cyber Security; Networking; Network Security; Machine Learning;
    Cloud Computing; IoT. Keywords: cyber security networking cloud computing IoT
    machine learning'
- source_sentence: My investigate involves security and privacy in ML systems
  sentences:
  - 'Supervisor: Mr/Ms Thamali Dassanayake. Department: DS. Research Cluster: CEAI.
    Research Interests: Big Data Management; Business Intelligence; Data Mining; Data
    Warehousing; Data Analytics. Keywords: big data BI data mining warehousing analytics'
  - 'Supervisor: Mr/Ms Kanishka Yapa. Department: CS. Research Cluster: IAS. Research
    Interests: Cyber Security; Critical Infrastructure Security; Healthcare Security;
    Threat Modeling; SDN. Keywords: cyber security critical infrastructure threat
    modeling SDN healthcare'
  - 'Supervisor: Mr/Ms S.M.B. Harshanath. Department: IT. Research Cluster: CEAI.
    Research Interests: Security and Privacy; Machine Learning; AI; Computer Vision.
    Keywords: security privacy machine learning AI computer vision'
- source_sentence: My research involves building a conversational AI chatbot
  sentences:
  - 'Supervisor: Mr/Ms Hanojhan Rajahrajasingh. Department: CSNE. Research Cluster:
    CI,AIMS. Research Interests: Wireless Communication; 6G Technology; Visible Light
    Communication. Keywords: wireless communication 6G visible light communication'
  - 'Supervisor: Professor Koliya Pulasinghe. Department: IT. Research Cluster: CEAI.
    Research Interests: Speech Recognition; Natural Language Understanding; Text-to-Speech;
    Dialogue Management; Speech Impairment Recognition; Conversational Interfaces.
    Keywords: NLP speech recognition TTS dialogue AI conversational'
  - 'Supervisor: Mr/Ms Vishan Jayasinghearachchi. Department: SE. Research Cluster:
    SST,CEAI. Research Interests: IoT; Edge Computing; Wireless Sensor Networks; Predictive
    Analytics; Wildlife Conservation; Environmental Monitoring. Keywords: IoT edge
    computing sensor networks predictive analytics environment'
pipeline_tag: sentence-similarity
library_name: sentence-transformers
metrics:
- cosine_accuracy
- cosine_accuracy_threshold
- cosine_f1
- cosine_f1_threshold
- cosine_precision
- cosine_recall
- cosine_ap
- cosine_mcc
model-index:
- name: SentenceTransformer based on sentence-transformers/all-MiniLM-L6-v2
  results:
  - task:
      type: binary-classification
      name: Binary Classification
    dataset:
      name: supervisor val
      type: supervisor_val
    metrics:
    - type: cosine_accuracy
      value: 0.972972972972973
      name: Cosine Accuracy
    - type: cosine_accuracy_threshold
      value: 0.8576409816741943
      name: Cosine Accuracy Threshold
    - type: cosine_f1
      value: 0.9855072463768115
      name: Cosine F1
    - type: cosine_f1_threshold
      value: 0.7122808694839478
      name: Cosine F1 Threshold
    - type: cosine_precision
      value: 0.9714285714285714
      name: Cosine Precision
    - type: cosine_recall
      value: 1.0
      name: Cosine Recall
    - type: cosine_ap
      value: 0.9991596638655463
      name: Cosine Ap
    - type: cosine_mcc
      value: 0.8047478161629564
      name: Cosine Mcc
---

# SentenceTransformer based on sentence-transformers/all-MiniLM-L6-v2

This is a [sentence-transformers](https://www.SBERT.net) model finetuned from [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2). It maps sentences & paragraphs to a 384-dimensional dense vector space and can be used for retrieval.

## Model Details

### Model Description
- **Model Type:** Sentence Transformer
- **Base model:** [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) <!-- at revision c9745ed1d9f207416be6d2e6f8de32d1f16199bf -->
- **Maximum Sequence Length:** 256 tokens
- **Output Dimensionality:** 384 dimensions
- **Similarity Function:** Cosine Similarity
- **Supported Modality:** Text
<!-- - **Training Dataset:** Unknown -->
<!-- - **Language:** Unknown -->
<!-- - **License:** Unknown -->

### Model Sources

- **Documentation:** [Sentence Transformers Documentation](https://sbert.net)
- **Repository:** [Sentence Transformers on GitHub](https://github.com/huggingface/sentence-transformers)
- **Hugging Face:** [Sentence Transformers on Hugging Face](https://huggingface.co/models?library=sentence-transformers)

### Full Model Architecture

```
SentenceTransformer(
  (0): Transformer({'transformer_task': 'feature-extraction', 'modality_config': {'text': {'method': 'forward', 'method_output_name': 'last_hidden_state'}}, 'module_output_name': 'token_embeddings', 'architecture': 'BertModel'})
  (1): Pooling({'embedding_dimension': 384, 'pooling_mode': 'mean', 'include_prompt': True})
  (2): Normalize({})
)
```

## Usage

### Direct Usage (Sentence Transformers)

First install the Sentence Transformers library:

```bash
pip install -U sentence-transformers
```
Then you can load this model and run inference.
```python
from sentence_transformers import SentenceTransformer

# Download from the 🤗 Hub
model = SentenceTransformer("sentence_transformers_model_id")
# Run inference
sentences = [
    'My research involves building a conversational AI chatbot',
    'Supervisor: Professor Koliya Pulasinghe. Department: IT. Research Cluster: CEAI. Research Interests: Speech Recognition; Natural Language Understanding; Text-to-Speech; Dialogue Management; Speech Impairment Recognition; Conversational Interfaces. Keywords: NLP speech recognition TTS dialogue AI conversational',
    'Supervisor: Mr/Ms Vishan Jayasinghearachchi. Department: SE. Research Cluster: SST,CEAI. Research Interests: IoT; Edge Computing; Wireless Sensor Networks; Predictive Analytics; Wildlife Conservation; Environmental Monitoring. Keywords: IoT edge computing sensor networks predictive analytics environment',
]
embeddings = model.encode(sentences)
print(embeddings.shape)
# [3, 384]

# Get the similarity scores for the embeddings
similarities = model.similarity(embeddings, embeddings)
print(similarities)
# tensor([[1.0000, 0.9051, 0.6934],
#         [0.9051, 1.0000, 0.6219],
#         [0.6934, 0.6219, 1.0000]])
```
<!--
### Direct Usage (Transformers)

<details><summary>Click to see the direct usage in Transformers</summary>

</details>
-->

<!--
### Downstream Usage (Sentence Transformers)

You can finetune this model on your own dataset.

<details><summary>Click to expand</summary>

</details>
-->

<!--
### Out-of-Scope Use

*List how the model may foreseeably be misused and address what users ought not to do with the model.*
-->

## Evaluation

### Metrics

#### Binary Classification

* Dataset: `supervisor_val`
* Evaluated with [<code>BinaryClassificationEvaluator</code>](https://sbert.net/docs/package_reference/sentence_transformer/evaluation.html#sentence_transformers.sentence_transformer.evaluation.BinaryClassificationEvaluator)

| Metric                    | Value      |
|:--------------------------|:-----------|
| cosine_accuracy           | 0.973      |
| cosine_accuracy_threshold | 0.8576     |
| cosine_f1                 | 0.9855     |
| cosine_f1_threshold       | 0.7123     |
| cosine_precision          | 0.9714     |
| cosine_recall             | 1.0        |
| **cosine_ap**             | **0.9992** |
| cosine_mcc                | 0.8047     |

<!--
## Bias, Risks and Limitations

*What are the known or foreseeable issues stemming from this model? You could also flag here known failure cases or weaknesses of the model.*
-->

<!--
### Recommendations

*What are recommendations with respect to the foreseeable issues? For example, filtering explicit content.*
-->

## Training Details

### Training Dataset

#### Unnamed Dataset

* Size: 210 training samples
* Columns: <code>sentence_0</code>, <code>sentence_1</code>, and <code>label</code>
* Approximate statistics based on the first 210 samples:
  |         | sentence_0                                                                        | sentence_1                                                                         | label                                                          |
  |:--------|:----------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------|:---------------------------------------------------------------|
  | type    | string                                                                            | string                                                                             | float                                                          |
  | details | <ul><li>min: 8 tokens</li><li>mean: 11.59 tokens</li><li>max: 17 tokens</li></ul> | <ul><li>min: 34 tokens</li><li>mean: 55.84 tokens</li><li>max: 74 tokens</li></ul> | <ul><li>min: 0.0</li><li>mean: 0.83</li><li>max: 1.0</li></ul> |
* Samples:
  | sentence_0                                                                     | sentence_1                                                                                                                                                                                                                                                                                                                                                                                    | label            |
  |:-------------------------------------------------------------------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------|
  | <code>My investigate involves agile development methodologies</code>           | <code>Supervisor: Professor Dasuni Nawinna. Department: ISE. Research Cluster: TIM,SST,CEAI. Research Interests: Technology Enhanced Learning; BPM; Social Network Analysis; Requirements Engineering; Social Capital. Keywords: e-learning BPM requirements engineering social networks</code>                                                                                               | <code>1.0</code> |
  | <code>I want to create recommender systems using ML</code>                     | <code>Supervisor: Doctor Kalpani Manathunga. Department: SE. Research Cluster: SST,TIM. Research Interests: Technology Enhanced Learning; Assistive Technologies; Personalized Learning Platforms; Recommender Systems; Learning Analytics; Educational Data Mining; Educational Psychology; HCI. Keywords: e-learning assistive technology recommender systems HCI learning analytics</code> | <code>1.0</code> |
  | <code>I am developing a peer review solution for university assignments</code> | <code>Supervisor: Mr/Ms Uthpala Samarakoon. Department: IT. Research Cluster: SST. Research Interests: E-Learning; HCI; Social Science; IT Education; Knowledge Management. Keywords: e-learning HCI social science knowledge management education</code>                                                                                                                                     | <code>1.0</code> |
* Loss: [<code>ContrastiveLoss</code>](https://sbert.net/docs/package_reference/sentence_transformer/losses.html#contrastiveloss) with these parameters:
  ```json
  {
      "distance_metric": "SiameseDistanceMetric.COSINE_DISTANCE",
      "margin": 0.5,
      "size_average": true
  }
  ```

### Training Hyperparameters
#### Non-Default Hyperparameters

- `per_device_train_batch_size`: 16
- `num_train_epochs`: 15
- `per_device_eval_batch_size`: 16
- `multi_dataset_batch_sampler`: round_robin

#### All Hyperparameters
<details><summary>Click to expand</summary>

- `per_device_train_batch_size`: 16
- `num_train_epochs`: 15
- `max_steps`: -1
- `learning_rate`: 5e-05
- `lr_scheduler_type`: linear
- `lr_scheduler_kwargs`: None
- `warmup_steps`: 0
- `optim`: adamw_torch_fused
- `optim_args`: None
- `weight_decay`: 0.0
- `adam_beta1`: 0.9
- `adam_beta2`: 0.999
- `adam_epsilon`: 1e-08
- `optim_target_modules`: None
- `gradient_accumulation_steps`: 1
- `average_tokens_across_devices`: True
- `max_grad_norm`: 1
- `label_smoothing_factor`: 0.0
- `bf16`: False
- `fp16`: False
- `bf16_full_eval`: False
- `fp16_full_eval`: False
- `tf32`: None
- `gradient_checkpointing`: False
- `gradient_checkpointing_kwargs`: None
- `torch_compile`: False
- `torch_compile_backend`: None
- `torch_compile_mode`: None
- `use_liger_kernel`: False
- `liger_kernel_config`: None
- `use_cache`: False
- `neftune_noise_alpha`: None
- `torch_empty_cache_steps`: None
- `auto_find_batch_size`: False
- `log_on_each_node`: True
- `logging_nan_inf_filter`: True
- `include_num_input_tokens_seen`: no
- `log_level`: passive
- `log_level_replica`: warning
- `disable_tqdm`: False
- `project`: huggingface
- `trackio_space_id`: trackio
- `per_device_eval_batch_size`: 16
- `prediction_loss_only`: True
- `eval_on_start`: False
- `eval_do_concat_batches`: True
- `eval_use_gather_object`: False
- `eval_accumulation_steps`: None
- `include_for_metrics`: []
- `batch_eval_metrics`: False
- `save_only_model`: False
- `save_on_each_node`: False
- `enable_jit_checkpoint`: False
- `push_to_hub`: False
- `hub_private_repo`: None
- `hub_model_id`: None
- `hub_strategy`: every_save
- `hub_always_push`: False
- `hub_revision`: None
- `load_best_model_at_end`: False
- `ignore_data_skip`: False
- `restore_callback_states_from_checkpoint`: False
- `full_determinism`: False
- `seed`: 42
- `data_seed`: None
- `use_cpu`: False
- `accelerator_config`: {'split_batches': False, 'dispatch_batches': None, 'even_batches': True, 'use_seedable_sampler': True, 'non_blocking': False, 'gradient_accumulation_kwargs': None}
- `parallelism_config`: None
- `dataloader_drop_last`: False
- `dataloader_num_workers`: 0
- `dataloader_pin_memory`: True
- `dataloader_persistent_workers`: False
- `dataloader_prefetch_factor`: None
- `remove_unused_columns`: True
- `label_names`: None
- `train_sampling_strategy`: random
- `length_column_name`: length
- `ddp_find_unused_parameters`: None
- `ddp_bucket_cap_mb`: None
- `ddp_broadcast_buffers`: False
- `ddp_backend`: None
- `ddp_timeout`: 1800
- `fsdp`: []
- `fsdp_config`: {'min_num_params': 0, 'xla': False, 'xla_fsdp_v2': False, 'xla_fsdp_grad_ckpt': False}
- `deepspeed`: None
- `debug`: []
- `skip_memory_metrics`: True
- `do_predict`: False
- `resume_from_checkpoint`: None
- `warmup_ratio`: None
- `local_rank`: -1
- `prompts`: None
- `batch_sampler`: batch_sampler
- `multi_dataset_batch_sampler`: round_robin
- `router_mapping`: {}
- `learning_rate_mapping`: {}

</details>

### Training Logs
| Epoch | Step | supervisor_val_cosine_ap |
|:-----:|:----:|:------------------------:|
| 1.0   | 14   | 0.9729                   |
| 2.0   | 28   | 0.9693                   |
| 3.0   | 42   | 0.9853                   |
| 4.0   | 56   | 0.9891                   |
| 5.0   | 70   | 0.9891                   |
| 6.0   | 84   | 0.9914                   |
| 7.0   | 98   | 0.9935                   |
| 8.0   | 112  | 0.9955                   |
| 9.0   | 126  | 0.9955                   |
| 10.0  | 140  | 0.9983                   |
| 11.0  | 154  | 0.9983                   |
| 12.0  | 168  | 0.9992                   |


### Training Time
- **Training**: 3.1 minutes

### Framework Versions
- Python: 3.13.0
- Sentence Transformers: 5.4.1
- Transformers: 5.5.4
- PyTorch: 2.11.0+cpu
- Accelerate: 1.13.0
- Datasets: 4.8.4
- Tokenizers: 0.22.2

## Citation

### BibTeX

#### Sentence Transformers
```bibtex
@inproceedings{reimers-2019-sentence-bert,
    title = "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks",
    author = "Reimers, Nils and Gurevych, Iryna",
    booktitle = "Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing",
    month = "11",
    year = "2019",
    publisher = "Association for Computational Linguistics",
    url = "https://arxiv.org/abs/1908.10084",
}
```

#### ContrastiveLoss
```bibtex
@inproceedings{hadsell2006dimensionality,
    author={Hadsell, R. and Chopra, S. and LeCun, Y.},
    booktitle={2006 IEEE Computer Society Conference on Computer Vision and Pattern Recognition (CVPR'06)},
    title={Dimensionality Reduction by Learning an Invariant Mapping},
    year={2006},
    volume={2},
    number={},
    pages={1735-1742},
    doi={10.1109/CVPR.2006.100}
}
```

<!--
## Glossary

*Clearly define terms in order to be accessible across audiences.*
-->

<!--
## Model Card Authors

*Lists the people who create the model card, providing recognition and accountability for the detailed work that goes into its construction.*
-->

<!--
## Model Card Contact

*Provides a way for people who have updates to the Model Card, suggestions, or questions, to contact the Model Card authors.*
-->