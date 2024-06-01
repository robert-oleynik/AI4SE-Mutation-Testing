import json
import os
import pathlib

import click

from ..collect.sample import Sample
from ..generator.repeat import RepeatGenerator

formatter = {"repeat": RepeatGenerator.format}


@click.command(help="Train a LLM model based on the data generated by `collect`")
@click.option(
    "-o",
    "--out-dir",
    default=pathlib.Path("out", "model"),
    type=pathlib.Path,
    show_default=True,
    help="Path to store trained model at",
)
@click.option(
    "-m",
    "--model-id",
    default="google/codegemma-1.1-2b",
    show_default=True,
    help="LLM model to train on",
)
@click.option(
    "--device",
    default="cuda:0",
    show_default=True,
    help="GPU device to run LLM model on",
)
@click.option(
    "-d",
    "--dataset",
    default=pathlib.Path("out", "dataset"),
    type=pathlib.Path,
    show_default=True,
    help="Dir to read datasets from",
)
@click.option("-g", "--generator", help="Generator format used for the dataset")
@click.option(
    "-l",
    "--learning-rate",
    default=3e-4,
    type=float,
    show_default=True,
    help="Learning rate used for LoRa training",
)
@click.option(
    "-n",
    "--num-epochs",
    default=2,
    type=int,
    show_default=True,
    help="Number of epochs to used for LoRa training",
)
@click.option(
    "-b",
    "--batch-size",
    default=4,
    type=int,
    show_default=True,
    help="Number of batches for LoRa training",
)
@click.option(
    "-t",
    "--test-size",
    default=0.1,
    type=float,
    show_default=True,
    help="Proportion of dataset used for testing/evaluation",
)
@click.option(
    "-s",
    "--seed",
    default=42,
    type=int,
    show_default=True,
    help="Seed used for randomness during training",
)
def train(
    out_dir,
    model_id,
    device,
    dataset,
    generator,
    learning_rate,
    num_epochs,
    batch_size,
    test_size,
    seed,
):
    import datasets

    prompts = []
    for p in os.listdir(path=dataset):
        if not p.endswith("json"):
            continue
        result = json.load((dataset / p).open("r"))
        if "samples" not in result:
            raise Exception("corrupted dataset")
        for name, samples in result["samples"].items():
            for i, s in enumerate(samples):
                print(f"\rfile: {p:<16}  {name}  [{i+1}/{len(samples)}] ", end="")
                sample = Sample(
                    s["commit"],
                    s["file"],
                    s["start"],
                    s["end"],
                    s["source"],
                    s["mutation"],
                )
                prompts.append(formatter[generator](sample))
            print()
    data = datasets.Dataset.from_dict({"prompt": prompts})

    import torch

    import mutator.ai.llm
    from mutator.ai.llm import LLM

    gpu = torch.device(device)

    mutator.ai.llm = LLM(device, model_id)

    # From provided JuypterLab
    def _tokenize(row):
        tokenizer = mutator.ai.llm.tokenizer
        source = row["prompt"]

        input_ids = tokenizer.encode(source) + [tokenizer.eos_token_id]
        labels = input_ids.copy()
        return {"input_ids": input_ids, "labels": labels}

    def _block(data, block_size=128):
        tokenizer = mutator.ai.llm.tokenizer
        concatenated = sum(data["input_ids"], [])
        length = len(concatenated)

        truncated_length = (length // block_size) * block_size
        blocked_ids = [
            concatenated[i : i + block_size]
            for i in range(0, truncated_length, block_size)
        ]

        pad_length = block_size - (length % block_size)
        if pad_length != block_size:
            blocked_ids += [
                concatenated[truncated_length:] + [tokenizer.eos_token_id] * pad_length
            ]
        assert len(blocked_ids) > 0
        return {"input_ids": blocked_ids, "labels": blocked_ids.copy()}

    tokenized_data = data.map(_tokenize, remove_columns=["prompt"])

    split_dataset = tokenized_data.train_test_split(
        test_size=0.1, shuffle=True, seed=42
    )
    test_data = split_dataset["test"]
    train_data = split_dataset["train"]

    test_data_blocks = test_data.map(_block, batched=True)
    train_data_blocks = train_data.map(_block, batched=True)

    import torch.optim
    from peft import LoraConfig, TaskType, get_peft_model
    from torch.utils.data import DataLoader
    from tqdm import tqdm
    from transformers import (
        DataCollatorForLanguageModeling,
        get_linear_schedule_with_warmup,
    )

    model = mutator.ai.llm.model
    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        inference_mode=False,
        target_modules=["q_proj", "v_proj"],
        r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        bias="all",
    )
    peft_model = get_peft_model(model, peft_config)
    peft_model.print_trainable_parameters()

    tokenizer = mutator.ai.llm.tokenizer
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
        tokenizer.pad_token = tokenizer.eos_token
    collator = DataCollatorForLanguageModeling(
        tokenizer, mlm=False, pad_to_multiple_of=8, return_tensors="pt"
    )
    train_dataloader = DataLoader(
        train_data_blocks, collate_fn=collator, batch_size=batch_size
    )
    eval_dataloader = DataLoader(
        test_data_blocks, collate_fn=collator, batch_size=batch_size
    )

    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    learning_rate_scheduler = get_linear_schedule_with_warmup(
        optimizer=optimizer,
        num_warmup_steps=0,
        num_training_steps=(len(train_dataloader) * num_epochs),
    )

    for epoch in range(num_epochs):
        model.train()
        total_loss = 0

        for _, batch in enumerate(tqdm(train_dataloader)):
            outputs = model(**batch.to(gpu))
            loss = outputs.loss
            total_loss += loss.detach().cpu().float()
            loss.backward()
            optimizer.step()
            learning_rate_scheduler.step()
            optimizer.zero_grad()

        model.eval()
        eval_loss = 0
        for _, batch in enumerate(tqdm(eval_dataloader)):
            with torch.no_grad():
                outputs = model(**batch.to(gpu))
            loss = outputs.loss
            eval_loss += loss.detach().cpu().float()

        eval_epoch_loss = eval_loss / len(eval_dataloader)
        train_epoch_loss = total_loss / len(train_dataloader)
        print(f"{epoch=}: {train_epoch_loss=} {eval_epoch_loss=}")

        peft_model.save_pretrained(out_dir / f"checkpoint-epoch-{epoch}")
