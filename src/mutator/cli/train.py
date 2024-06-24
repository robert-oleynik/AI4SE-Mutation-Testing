import math
import os
import pathlib
import shutil

import click


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
    default=pathlib.Path("out", "dataset", "data"),
    type=pathlib.Path,
    show_default=True,
    help="Dir to read datasets from",
)
@click.option(
    "-l",
    "--learning-rate",
    default=1e-4,
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
    help="Number of batches for LoRa training [Bugged]",
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
@click.option("--alpha", default=16, type=int, show_default=True, help="TODO")
@click.option("--dropout", default=0.05, type=float, show_default=True, help="TODO")
@click.option("--rank", default=8, type=int, show_default=True, help="TODO")
def train(
    out_dir,
    model_id,
    device,
    dataset,
    learning_rate,
    num_epochs,
    batch_size,
    test_size,
    seed,
    alpha,
    dropout,
    rank,
):
    import datasets
    import torch
    import torch.utils.data
    import tqdm
    import transformers

    data = datasets.load_from_disk(dataset_path=dataset.absolute().__str__())
    data = datasets.Dataset.from_dict({"prompt": data["prompt"]})

    device = torch.device(device)
    tokenizer = transformers.GemmaTokenizer.from_pretrained(model_id)
    model = transformers.AutoModelForCausalLM.from_pretrained(
        model_id, device_map=device, torch_dtype=torch.float16
    )

    def _tokenize(row):
        tokens = tokenizer(row["prompt"] + "<eos>")
        labels = tokens.input_ids.copy()
        return {**tokens, "labels": labels}

    tokenized_data = data.map(_tokenize)
    tokenized_data = tokenized_data.remove_columns(["prompt"])
    print(tokenized_data)

    data_collator = transformers.DataCollatorForLanguageModeling(
        tokenizer, mlm=False, pad_to_multiple_of=8, return_tensors="pt"
    )

    split_dataset = tokenized_data.train_test_split(
        test_size=test_size, shuffle=True, seed=seed
    )
    test_data = split_dataset["test"]
    train_data = split_dataset["train"]

    import torch.utils.data

    train_dataloader = torch.utils.data.DataLoader(
        train_data, collate_fn=data_collator, batch_size=batch_size
    )
    test_dataloader = torch.utils.data.DataLoader(
        test_data, collate_fn=data_collator, batch_size=batch_size
    )

    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    lr_scheduler = transformers.get_linear_schedule_with_warmup(
        optimizer=optimizer,
        num_warmup_steps=0,
        num_training_steps=len(train_dataloader) * num_epochs,
    )

    from peft import LoraConfig, TaskType

    peft_config = LoraConfig(
        lora_alpha=alpha,
        lora_dropout=dropout,
        inference_mode=False,
        target_modules=["q_proj", "v_proj"],
        r=rank,
        bias="all",
        task_type=TaskType.CAUSAL_LM,
    )
    model.add_adapter(peft_config)

    epoch_train_loss = []
    epoch_test_loss = []
    for epoch in range(num_epochs):
        model.train()
        train_loss = 0
        for step, batch in enumerate(tqdm.tqdm(train_dataloader)):
            outputs = model(**batch.to(device))
            loss = outputs.loss
            train_loss += loss.detach().cpu().float()
            if math.isnan(train_loss):
                print(tokenizer.decode(batch))
                print(loss.detach().cpu().float())
                raise ValueError("training reach NaN")
            loss.backward()
            optimizer.step()
            lr_scheduler.step()
            optimizer.zero_grad()
            if step % 200 == 199:
                inter_train_loss = train_loss / step
                msg = f"{step=} loss={inter_train_loss.item()}"
                columns = os.get_terminal_size().columns
                print(f"\r{{:<{columns}}}".format(msg))

        model.eval()
        test_loss = 0
        for step, batch in enumerate(tqdm.tqdm(test_dataloader)):
            with torch.no_grad():
                outputs = model(**batch.to(device))
            loss = outputs.loss
            test_loss += loss.detach().cpu().float()

        test_epoch_loss = test_loss / len(test_dataloader)
        train_epoch_loss = train_loss / len(train_dataloader)
        print(f"{epoch=}: {train_epoch_loss=} {test_epoch_loss=}")

        epoch_train_loss.append(train_epoch_loss)
        epoch_test_loss.append((test_epoch_loss, epoch))

        model.save_pretrained(str(out_dir / "checkpoints" / str(epoch)))

    sorted_epochs = epoch_test_loss.copy()
    sorted_epochs.sort()
    _, best_epoch = sorted_epochs[0]

    print("Results:")
    for j in range(num_epochs):
        print(f"{j}: train_loss={sorted_epochs[j]} test_loss={sorted_epochs[j]}")
    print(f"best epoch: {best_epoch}")
    shutil.rmtree(out_dir / "final")
    shutil.copy(out_dir / "checkpoints" / str(best_epoch), out_dir / "final")

    #    from transformers import Trainer, TrainingArguments
    #    args = TrainingArguments(
    #        output_dir=out_dir.__str__(),
    #        learning_rate=learning_rate,
    #        per_device_train_batch_size=batch_size,
    #        per_device_eval_batch_size=batch_size,
    #        num_train_epochs=num_epochs,
    #        weight_decay=0.01,
    #        eval_strategy="epoch",
    #        save_strategy="epoch",
    #        load_best_model_at_end=True,
    #        push_to_hub=False,
    #    )
    #
    #    trainer = Trainer(
    #        model=model,
    #        args=args,
    #        train_dataset=train_data,
    #        eval_dataset=test_data,
    #        tokenizer=tokenizer,
    #        data_collator=data_collator,
    #    )
    #
    #    trainer.train()
