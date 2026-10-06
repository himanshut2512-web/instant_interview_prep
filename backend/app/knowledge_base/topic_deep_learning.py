from ._build import P, Q, S, T, md, note

TOPIC = {
    "key": "deep_learning",
    "name": "Deep Learning",
    "keywords": ["deep learning", "neural network", "neural networks", "pytorch", "tensorflow", "keras", "cnn",
                 "rnn", "lstm", "transformer", "transformers", "computer vision", "image", "gpu", "bert"],
    "core": ["deep learning", "pytorch", "tensorflow", "computer vision"],
    "subtopics": ["Backpropagation & optimisers", "Activations & losses", "Regularisation (dropout, batch norm)",
                  "CNNs", "RNNs/LSTMs", "Attention & transformers", "Transfer learning", "Model compression"],
    "revision": note(
        summary="Deep-learning questions check the mechanics (forward/backward pass, optimisers, losses), the "
        "standard fixes for training problems, the core architectures (CNN, RNN, transformer) and practical "
        "skills like transfer learning and deployment.",
        concepts=[
            ("Backpropagation", "Chain rule applied backwards through the computation graph to get the gradient of "
             "the loss for every weight."),
            ("Optimisers", "SGD, SGD+momentum, RMSProp, Adam/AdamW (adaptive per-parameter learning rates; AdamW "
             "decouples weight decay)."),
            ("Activations", "ReLU (default hidden), GELU (transformers), sigmoid (binary output), softmax "
             "(multi-class output), tanh."),
            ("Losses", "Cross-entropy for classification, MSE/MAE/Huber for regression, contrastive losses for "
             "embeddings."),
            ("Vanishing / exploding gradients", "Gradients shrink or blow up through many layers - fixed with ReLU, "
             "good init, residual connections, normalisation, gradient clipping."),
            ("Batch norm / layer norm", "Normalise activations to stabilise and speed up training; layer norm is "
             "used in transformers."),
            ("Dropout", "Randomly zeroes activations during training to reduce co-adaptation; off at inference."),
            ("CNN", "Convolutions share weights across space to detect local patterns; pooling adds invariance."),
            ("Self-attention", "softmax(QK^T / sqrt(d_k)) V - each token attends to all others; parallelisable."),
            ("Transfer learning", "Start from a pre-trained model; freeze or fine-tune layers on your task."),
        ],
        explanation=md("""
            **Training loop.** forward pass -> loss -> `loss.backward()` (backprop) -> `optimizer.step()` ->
            `optimizer.zero_grad()`. Use `model.train()` / `model.eval()` to switch dropout and batch-norm
            behaviour, and `torch.no_grad()` for evaluation.

            **Learning rate is the most important hyper-parameter.** Too high -> divergence/NaN; too low -> slow.
            Use warm-up plus cosine or step decay, and an LR finder for new problems.

            **Diagnosing training curves.**

            | Symptom | Likely cause | Fix |
            |---|---|---|
            | Train and val loss both high | Underfitting | Bigger model, train longer, higher LR |
            | Train low, val rising | Overfitting | Augmentation, dropout, weight decay, early stopping, more data |
            | Loss NaN / spikes | LR too high, exploding gradients, bad inputs | Lower LR, clip gradients, check data |
            | Loss flat from the start | Bug or dead units | Overfit one batch first; check labels & LR |

            **Architectures.** CNNs for images (ResNet's skip connections enabled very deep nets), RNN/LSTM/GRU for
            sequences (gates fight vanishing gradients but are sequential), transformers for almost everything now
            (self-attention + positional encodings, parallel training, scales with data).

            **Transfer learning.** Freeze the backbone and train a new head when data is small; progressively
            unfreeze with a lower learning rate for more data; parameter-efficient methods (LoRA, adapters) for
            large models.

            **Deployment.** Export to ONNX/TorchScript, quantise (INT8), prune or distil into a smaller student
            model, batch requests, and benchmark latency on target hardware.
        """),
        code=md("""
            import torch
            from torch import nn

            model = nn.Sequential(nn.Linear(20, 64), nn.ReLU(), nn.Dropout(0.2), nn.Linear(64, 2))
            opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-2)
            loss_fn = nn.CrossEntropyLoss()

            for epoch in range(10):
                model.train()
                for xb, yb in train_loader:
                    opt.zero_grad()
                    loss = loss_fn(model(xb), yb)
                    loss.backward()
                    nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                    opt.step()
                model.eval()
                with torch.no_grad():
                    val_acc = sum((model(x).argmax(1) == y).sum().item() for x, y in val_loader) / len(val_ds)
                print(epoch, round(val_acc, 4))
        """),
        language="python",
        pitfalls=[
            "Forgetting model.eval() at inference (dropout and batch norm behave differently).",
            "Forgetting optimizer.zero_grad() so gradients accumulate across steps.",
            "Applying softmax before nn.CrossEntropyLoss (it expects raw logits).",
            "Not normalising inputs the same way the pre-trained model expects.",
            "Judging a model by training accuracy without a validation curve.",
        ],
        tips=[
            "Explain intuition first (what the layer/trick does), then maths if asked.",
            "Mention the debugging habit of overfitting a single batch first.",
            "Relate architecture choices to data size, latency and cost constraints.",
            "Know one architecture deeply (e.g. ResNet or BERT) including why it works.",
        ],
        cheat_sheet=[
            "Adam default lr is about 1e-3; fine-tuning transformers often uses 1e-5 to 5e-5.",
            "Receptive field grows with depth and stride in CNNs.",
            "LSTM gates: forget, input, output; GRU: update, reset.",
            "Attention cost is O(n^2) in sequence length.",
            "Batch norm uses batch statistics in training and running averages at inference.",
            "Early stopping = stop when validation loss stops improving for N epochs.",
        ],
        likely_questions=[
            "Explain backpropagation.",
            "How do you handle vanishing gradients?",
            "Why do we need activation functions?",
            "Explain self-attention and transformers.",
            "What is transfer learning and when do you fine-tune?",
        ],
    ),
    "theory": [
        T("beginner", "Explain backpropagation and gradient descent in simple terms.",
          """
          A neural network makes a prediction (forward pass) and a **loss** measures how wrong it is. Training
          means adjusting weights to reduce that loss.

          **Backpropagation** computes how much each weight contributed to the loss: it applies the chain rule
          backwards from the output layer to the input layer, reusing intermediate results, so we get the gradient
          dLoss/dw for every weight in one backward pass.

          **Gradient descent** then updates each weight a small step against its gradient:
          `w = w - learning_rate * gradient`. In practice we use **mini-batches** (stochastic gradient descent)
          and optimisers like momentum or Adam that adapt the step size.

          Analogy: walking downhill in fog - the gradient tells you the steepest downward direction where you
          stand, and the learning rate is your step size.
          """,
          ["Forward pass + loss", "Chain rule backwards", "Update rule", "Mini-batch / optimisers"],
          "Use the downhill analogy, then show the update formula - simple and confident.",
          ["What happens if the learning rate is too high?", "What does Adam add over SGD?"], hot=True),
        T("beginner", "Why do neural networks need non-linear activation functions? Compare ReLU and sigmoid.",
          """
          Without non-linear activations, stacking layers collapses into a single linear transformation - the
          network could only learn linear relationships no matter how deep it is.

          - **Sigmoid** squashes to (0, 1); good for a binary output probability, but it saturates for large
            |x| so gradients vanish in deep hidden layers, and outputs aren't zero-centred.
          - **ReLU** = max(0, x): cheap, doesn't saturate for positive inputs, gives sparse activations and much
            faster training - the default for hidden layers. Downside: "dying ReLU" units stuck at zero; Leaky
            ReLU/GELU address this.
          - **Softmax** turns logits into a probability distribution across classes for multi-class outputs.
          """,
          ["Linear collapse argument", "Sigmoid saturation", "ReLU benefits and dying ReLU", "Output-layer choices"],
          "State the 'stacked linear layers are still linear' argument in one line - it's the key insight.",
          ["What is GELU and where is it used?", "Why not use sigmoid in hidden layers?"]),
        T("intermediate", "What are vanishing and exploding gradients, and how do you fix them?",
          """
          During backprop, gradients are multiplied layer by layer. If those factors are mostly < 1 (e.g. saturated
          sigmoids), gradients **vanish** and early layers stop learning; if > 1, they **explode**, causing huge
          updates, NaNs and divergence. RNNs over long sequences suffer most.

          Fixes:
          - ReLU-family activations instead of sigmoid/tanh in hidden layers.
          - Careful initialisation (He for ReLU, Xavier/Glorot for tanh).
          - **Residual connections** (ResNet, transformers) give gradients a direct path.
          - Batch/layer normalisation.
          - **Gradient clipping** (by norm) for exploding gradients, especially in RNNs.
          - LSTM/GRU gates or transformers instead of vanilla RNNs.
          - Lower learning rate / warm-up.
          """,
          ["Mechanism via repeated multiplication", "Symptoms of each", "Architectural fixes", "Clipping & init"],
          "Mention residual connections - they are the modern, most important fix.",
          ["Why do residual connections help?", "How does LSTM's cell state help?"], hot=True),
        T("intermediate", "What do batch normalisation and dropout do, and how do they behave at inference?",
          """
          **Batch normalisation** normalises each feature of a layer's inputs using the mini-batch mean and variance,
          then applies learnable scale and shift. It stabilises training, allows higher learning rates and adds mild
          regularisation. At **inference** it uses running averages collected during training, so predictions
          don't depend on the batch. Layer norm (normalising across features of one sample) is preferred in
          transformers and with small batches.

          **Dropout** randomly zeroes a fraction p of activations during training, forcing redundant
          representations and reducing overfitting. At **inference** it is turned off (PyTorch scales activations
          during training - "inverted dropout" - so no rescaling is needed later).

          Both depend on mode, which is why `model.eval()` before inference is essential.
          """,
          ["How BN works + benefits", "BN at inference uses running stats", "Dropout mechanism", "eval() importance"],
          "Mention a bug you avoided or fixed by calling model.eval() - shows practical experience.",
          ["Why is layer norm used in transformers?", "Can dropout and batch norm conflict?"]),
        T("advanced", "Explain self-attention and the transformer architecture. Why did it replace RNNs?",
          """
          **Self-attention** lets every token look at every other token. Each token is projected into a query (Q),
          key (K) and value (V); attention weights are `softmax(QK^T / sqrt(d_k))`, and the output is the weighted
          sum of values. Dividing by sqrt(d_k) keeps dot products from growing with dimension and saturating the
          softmax. **Multi-head** attention runs several attention functions in parallel to capture different
          relations.

          A transformer block = multi-head attention + position-wise feed-forward network, each wrapped with
          residual connections and layer norm. Positional encodings (sinusoidal, learned or rotary) inject order.
          Encoder-only models (BERT) suit understanding tasks; decoder-only models (GPT-style) generate text with
          causal masking; encoder-decoder models (T5) map sequences to sequences.

          Why it won over RNNs: training is **parallel** across the sequence (no step-by-step recurrence), long-range
          dependencies are one hop away, and it scales well with data and compute. Cost: attention is O(n^2) in
          sequence length, addressed by efficient attention variants and caching.
          """,
          ["Q/K/V and the formula", "Why scale by sqrt(d_k)", "Block structure (residual + norm + FFN)",
           "Encoder/decoder variants", "Parallelism vs RNNs and O(n^2) cost"],
          "Walk through one token attending to others in a sentence - concrete beats abstract.",
          ["What is masked attention?", "What are positional encodings?", "What is the KV cache?"], hot=True),
        T("advanced", "When and how do you use transfer learning and fine-tuning?",
          """
          Transfer learning reuses a model pre-trained on a large dataset (ImageNet, web text) because its early
          layers learn general features (edges, textures, syntax) that transfer to new tasks.

          Strategy depends on data size and similarity:
          - **Little data, similar domain**: freeze the backbone, train only a new head (feature extraction).
          - **Moderate data**: unfreeze the top blocks and fine-tune with a small learning rate (often
            discriminative LRs - smaller for lower layers).
          - **Lots of data / different domain** (e.g. X-rays): fine-tune most or all layers.
          - **Large language models**: parameter-efficient fine-tuning (LoRA/QLoRA, adapters) trains a tiny
            fraction of parameters; often prompt engineering or RAG is enough before fine-tuning at all.

          Practicalities: match the original preprocessing/normalisation, use augmentation, watch for catastrophic
          forgetting, and compare against a from-scratch baseline when the domain is very different.
          """,
          ["Why transfer works", "Freeze vs fine-tune decision", "Learning-rate strategy", "PEFT/LoRA for LLMs"],
          "Frame it as a decision matrix (data size x domain similarity).",
          ["What is LoRA?", "What is catastrophic forgetting?", "When is fine-tuning an LLM not worth it?"]),
    ],
    "practical": [
        P("beginner", "Write a minimal PyTorch training and evaluation loop for a classifier.",
          """
          You have `train_loader` and `val_loader` DataLoaders yielding `(x, y)` batches and a model `net`.
          Train for 5 epochs with Adam and print validation accuracy each epoch.
          """,
          ["Pick loss (CrossEntropyLoss on logits) and optimiser.", "train(): zero_grad -> forward -> loss -> "
           "backward -> step.", "eval() + no_grad() for validation.", "Track metrics per epoch."],
          "The loop shows the standard order of operations. CrossEntropyLoss expects raw logits, and evaluation "
          "runs without gradient tracking in eval mode.",
          """
          import torch
          from torch import nn

          device = "cuda" if torch.cuda.is_available() else "cpu"
          net = net.to(device)
          loss_fn = nn.CrossEntropyLoss()
          opt = torch.optim.Adam(net.parameters(), lr=1e-3)

          for epoch in range(5):
              net.train()
              for x, y in train_loader:
                  x, y = x.to(device), y.to(device)
                  opt.zero_grad()
                  loss = loss_fn(net(x), y)
                  loss.backward()
                  opt.step()

              net.eval()
              correct = total = 0
              with torch.no_grad():
                  for x, y in val_loader:
                      x, y = x.to(device), y.to(device)
                      correct += (net(x).argmax(dim=1) == y).sum().item()
                      total += y.numel()
              print(f"epoch {epoch}: loss={loss.item():.4f} val_acc={correct / total:.3f}")
          """, "python",
          "O(epochs x dataset size x forward/backward cost).",
          ["Empty validation set", "Class imbalance (accuracy misleading)", "Device mismatch errors"],
          "Narrate the purpose of each line - zero_grad and eval() are what interviewers check.",
          ["How would you add early stopping?", "How would you use mixed precision?"], hot=True),
        P("intermediate", "Implement scaled dot-product attention (with an optional mask).",
          """
          Inputs: Q, K, V tensors of shape (batch, seq_len, d_k). Optional boolean mask (batch, seq_len, seq_len)
          where False means "do not attend". Return the outputs and attention weights.
          """,
          ["Scores = Q K^T / sqrt(d_k).", "Apply mask by setting blocked scores to -inf.",
           "Softmax over the key dimension.", "Weighted sum of V."],
          "This is the core of every transformer layer. The mask supports padding and causal (no-peeking) "
          "attention.",
          """
          import math
          import torch

          def scaled_dot_product_attention(Q, K, V, mask=None):
              d_k = Q.size(-1)
              scores = Q @ K.transpose(-2, -1) / math.sqrt(d_k)        # (batch, seq, seq)
              if mask is not None:
                  scores = scores.masked_fill(~mask, float("-inf"))
              weights = torch.softmax(scores, dim=-1)
              return weights @ V, weights

          # causal mask example
          seq = 4
          causal = torch.tril(torch.ones(seq, seq, dtype=torch.bool)).unsqueeze(0)
          Q = K = V = torch.randn(1, seq, 8)
          out, w = scaled_dot_product_attention(Q, K, V, causal)
          print(out.shape, w[0])
          """, "python",
          "O(n^2 * d) time and O(n^2) memory for sequence length n.",
          ["A row that is fully masked (softmax of all -inf gives NaN)", "Very long sequences (memory)",
           "Numerical stability in half precision"],
          "Mention why we scale by sqrt(d_k) and what the causal mask does.",
          ["How does multi-head attention extend this?", "How does a KV cache speed up generation?"], hot=True),
        P("advanced", "Fine-tune a pre-trained image model on a small dataset (2,000 images, 5 classes).",
          """
          Images are in `data/train/<class>/` and `data/val/<class>/`. Use torchvision. Explain your freezing
          strategy, augmentation and learning rates.
          """,
          ["Load a pre-trained backbone (e.g. ResNet-50) and replace the head.",
           "Stage 1: freeze backbone, train head with a higher LR.",
           "Stage 2: unfreeze the last block and fine-tune with a lower LR.",
           "Augment training data; use the backbone's normalisation."],
          "With only 2,000 images, training only the head first avoids destroying pre-trained features; "
          "unfreezing the last block afterwards adapts higher-level features to the new classes.",
          """
          import torch
          from torch import nn
          from torchvision import datasets, models, transforms

          weights = models.ResNet50_Weights.DEFAULT
          train_tf = transforms.Compose([
              transforms.RandomResizedCrop(224), transforms.RandomHorizontalFlip(),
              transforms.ColorJitter(0.2, 0.2), transforms.ToTensor(),
              transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
          ])
          train_ds = datasets.ImageFolder("data/train", transform=train_tf)
          val_ds = datasets.ImageFolder("data/val", transform=weights.transforms())

          model = models.resnet50(weights=weights)
          for p in model.parameters():
              p.requires_grad = False                                  # stage 1: freeze backbone
          model.fc = nn.Linear(model.fc.in_features, len(train_ds.classes))
          opt = torch.optim.AdamW(model.fc.parameters(), lr=1e-3)
          # ... train a few epochs ...

          for p in model.layer4.parameters():
              p.requires_grad = True                                   # stage 2: unfreeze last block
          opt = torch.optim.AdamW([
              {"params": model.layer4.parameters(), "lr": 1e-4},
              {"params": model.fc.parameters(), "lr": 5e-4},
          ], weight_decay=1e-2)
          # ... continue training with early stopping on val loss ...
          """, "python",
          "Stage 1 is cheap (only the head gets gradients); stage 2 costs more per step.",
          ["Class imbalance (use weighted loss or sampler)", "Domain very different from ImageNet",
           "Data leakage via near-duplicate images across splits"],
          "Justify the two-stage approach with the data size - that reasoning is what is being assessed.",
          ["How would you handle 50 images per class?", "When would you train from scratch?"]),
    ],
    "scenario": [
        S("beginner", """
          While training an image classifier, training loss keeps falling but validation loss starts rising after
          epoch 5, and validation accuracy plateaus at 78%.
          """,
          "What is happening and what do you do?",
          [("Diagnose", "Classic overfitting - the model memorises training images."),
           ("Quick wins", "Early stopping on validation loss; keep the best checkpoint."),
           ("Regularise", "Data augmentation, dropout, weight decay."),
           ("Data", "Collect/label more data, check label quality and class balance."),
           ("Model", "Use transfer learning or a smaller model; tune the learning rate.")],
          """
          The diverging curves after epoch 5 are textbook **overfitting**: the network keeps fitting training
          specifics that don't generalise.

          Immediately I'd add **early stopping** and keep the checkpoint with the best validation loss. Then I'd
          regularise: stronger data augmentation (random crops, flips, colour jitter), dropout before the
          classifier head and weight decay with AdamW.

          I'd also look at the data: are some classes tiny, are there mislabelled images, are train/val images
          near-duplicates? If the model was trained from scratch, switching to a pre-trained backbone usually gives
          a big jump on small datasets. I'd track each change's effect on validation accuracy one at a time.
          """,
          ["Reads the learning curves correctly", "Knows early stopping & regularisation", "Checks data quality",
           "Changes one thing at a time"],
          ["Training longer", "Evaluating on the training set", "Changing many things at once"],
          ["How does augmentation reduce overfitting?", "How would you pick the dropout rate?"]),
        S("intermediate", """
          Halfway through training a text model, the loss suddenly becomes NaN. It happens around the same step
          every run.
          """,
          "How do you debug it?",
          [("Reproduce", "Fix seeds; find the exact step and batch where it happens."),
           ("Inspect data", "Check that batch for NaN/inf, empty sequences, extreme values, bad labels."),
           ("Check numerics", "log(0), division by zero, fp16 overflow - use stable loss functions."),
           ("Stabilise", "Lower LR or add warm-up, clip gradients, use loss scaling for mixed precision."),
           ("Monitor", "Log gradient norms and loss per step to catch spikes early.")],
          """
          Because it happens at the same step every time, I'd suspect a **specific batch** rather than random
          instability. I'd log the batch index, then inspect that batch: NaN or infinite feature values, an empty
          sequence that makes a mean-pool divide by zero, or a label outside the class range.

          If the data is clean, I'd look at numerics: a custom loss using `log(p)` without clamping, or fp16
          overflow in mixed precision - use `BCEWithLogitsLoss`/`CrossEntropyLoss` on logits and a GradScaler.
          I'd log the gradient norm per step; a spike before the NaN points to exploding gradients, fixed by
          gradient clipping (e.g. max_norm=1.0), a lower learning rate or a warm-up schedule.

          I'd add `torch.autograd.set_detect_anomaly(True)` temporarily to locate the operation producing NaN,
          then add a data validation step so bad records are filtered before training.
          """,
          ["Notices the deterministic pattern", "Checks data first", "Knows numeric-stability pitfalls",
           "Uses clipping/LR/warm-up and monitoring"],
          ["Just restarting training", "Lowering the LR without finding the cause", "Ignoring mixed-precision issues"],
          ["What does gradient clipping do exactly?", "How does a GradScaler work?"], hot=True),
        S("advanced", """
          Your 98 MB image model runs at 400 ms per image on a mid-range phone, but the product needs under 50 ms
          and an app download budget of 20 MB, with at most a 2-point accuracy drop.
          """,
          "How would you get there?",
          [("Profile", "Measure latency per layer on the target device, not a laptop."),
           ("Smaller architecture", "MobileNetV3/EfficientNet-Lite as the student."),
           ("Distil", "Knowledge distillation from the large teacher to keep accuracy."),
           ("Compress", "INT8 quantisation (post-training or QAT), pruning."),
           ("Deploy & verify", "TFLite/Core ML/ONNX Runtime with hardware delegates; A/B on accuracy & latency.")],
          """
          A 8x latency cut won't come from one trick, so I'd combine several and measure on the real phone.

          First, profile per layer on the device to see whether compute or memory bandwidth dominates. Then pick
          a mobile-first architecture such as MobileNetV3 or EfficientNet-Lite and **distil** knowledge from the
          current model (teacher) into it - training the student on the teacher's soft labels usually recovers
          most of the accuracy gap.

          Next, **INT8 quantisation**: post-training quantisation with a calibration set gives ~4x smaller weights
          and big speed-ups on mobile NPUs/DSPs; if accuracy drops more than 2 points, use quantisation-aware
          training. Structured pruning can cut further. Export to TFLite/Core ML and use the GPU/NNAPI delegate.

          I'd track three numbers for every variant - accuracy, p95 latency on the device, and model size - and
          ship the smallest one that meets all three, with on-device telemetry to verify in the field.
          """,
          ["Measures on target hardware", "Combines architecture, distillation, quantisation, pruning",
           "Manages the accuracy budget", "Clear success criteria"],
          ["Testing latency only on a laptop GPU", "Only quantising and hoping", "Ignoring the accuracy constraint"],
          ["What is knowledge distillation?", "Post-training quantisation vs QAT?"]),
    ],
    "quiz": [
        Q("beginner", "Why do neural networks use non-linear activation functions?",
          ["To speed up data loading", "So stacked layers can model non-linear relationships",
           "To reduce the number of parameters", "To normalise the inputs"], 1,
          "Without non-linearities, any stack of linear layers is equivalent to a single linear layer.",
          ["Unrelated to activations.", "Correct.", "Activations add no parameters reduction.",
           "That is normalisation's job."],
          "A one-line justification ('linear layers compose to a linear map') is enough.", hot=True),
        Q("beginner", "Which output activation gives class probabilities that sum to 1 for multi-class "
          "classification?",
          ["ReLU", "Sigmoid", "Softmax", "Tanh"], 2,
          "Softmax exponentiates logits and normalises them into a probability distribution.",
          ["ReLU is unbounded.", "Sigmoid outputs independent probabilities (multi-label).", "Correct.",
           "Tanh outputs (-1, 1)."],
          "Note that PyTorch's CrossEntropyLoss applies log-softmax internally."),
        Q("intermediate", "What happens to dropout when you call model.eval() in PyTorch?",
          ["Dropout rate doubles", "Dropout is disabled", "Weights are re-initialised", "Nothing changes"], 1,
          "In eval mode dropout layers pass activations through unchanged (inverted dropout already scaled them "
          "during training).",
          ["No.", "Correct.", "No.", "eval() changes dropout and batch-norm behaviour."],
          "Forgetting eval() is a classic production bug worth mentioning."),
        Q("intermediate", "Which technique directly addresses exploding gradients in RNN training?",
          ["Gradient clipping", "Increasing the learning rate", "Removing the bias terms", "Using sigmoid everywhere"],
          0,
          "Clipping rescales gradients whose norm exceeds a threshold, preventing huge destabilising updates.",
          ["Correct.", "Makes it worse.", "Unrelated.", "Sigmoids worsen vanishing gradients."],
          "Mention clipping by norm and typical values like 1.0 or 5.0.", hot=True),
        Q("advanced", "In scaled dot-product attention, why are scores divided by sqrt(d_k)?",
          ["To make attention sparse", "To keep dot products from growing large and saturating the softmax",
           "To normalise the values V", "To reduce memory usage"], 1,
          "Dot products of d_k-dimensional vectors grow with d_k; large logits push softmax into regions with "
          "tiny gradients. Scaling keeps the variance around 1.",
          ["Scaling doesn't create sparsity.", "Correct.", "V is not scaled.", "Memory is unaffected."],
          "Expect a follow-up on what multi-head attention adds.", hot=True),
    ],
}
