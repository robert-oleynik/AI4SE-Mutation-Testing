import hashlib
import math
import os
import pathlib
import shutil

import click

from ..helper.timed import timed


@click.command(
    help="""
    Train a LLM model based on the data generated by `collect`.
    Will use the LoRa method for training.
    """
)
@click.option(
    "-o",
    "--out-dir",
    default=pathlib.Path("out", "model"),
    type=pathlib.Path,
    show_default=True,
    help="Path to store trained model in.",
)
@click.option(
    "-m",
    "--model-id",
    default="google/codegemma-1.1-2b",
    show_default=True,
    help="LLM model used for training.",
)
@click.option(
    "--device",
    default="cuda:0",
    show_default=True,
    help="GPU device to run LLM and training on.",
)
@click.option(
    "-d",
    "--dataset",
    default=pathlib.Path("out", "dataset", "data"),
    type=pathlib.Path,
    show_default=True,
    help="""
    Path to dataset's data directory. This is equal to the subpath `/data` of the
    dataset directory specified with the `collect` subcommand.
    """,
)
@click.option(
    "-l",
    "--learning-rate",
    default=1e-4,
    type=float,
    show_default=True,
    help="Learning rate used for LoRa training.",
)
@click.option(
    "-n",
    "--num-epochs",
    default=2,
    type=int,
    show_default=True,
    help="Number of epochs to used for LoRa training.",
)
@click.option(
    "-t",
    "--test-size",
    default=0.1,
    type=float,
    show_default=True,
    help="Proportion of dataset used for testing/evaluation.",
)
@click.option(
    "-s",
    "--seed",
    default=42,
    type=int,
    show_default=True,
    help="Seed randomness, used for splitting the train and test/eval dataset.",
)
@click.option(
    "--alpha",
    default=16,
    type=int,
    show_default=True,
    help="Set the alpha value for LoRa training.",
)
@click.option(
    "--dropout",
    default=0.05,
    type=float,
    show_default=True,
    help="Set the dropout value for LoRa training.",
)
@click.option(
    "--rank",
    default=8,
    type=int,
    show_default=True,
    help="Set the rank value for LoRa training.",
)
@timed
def train(
    out_dir,
    model_id,
    device,
    dataset,
    learning_rate,
    num_epochs,
    test_size,
    seed,
    alpha,
    dropout,
    rank,
):
    import datasets
    import pandas
    import torch
    import torch.utils.data
    import tqdm
    import transformers

    batch_size = 1

    data = datasets.load_from_disk(dataset_path=dataset.absolute().__str__())
    data = datasets.Dataset.from_dict({"prompt": data["prompt"]})
    print(data)

    device = torch.device(device)
    tokenizer = transformers.GemmaTokenizer.from_pretrained(model_id)
    model = transformers.AutoModelForCausalLM.from_pretrained(
        model_id, device_map=device, torch_dtype=torch.float16
    )

    def _tokenize(row):
        hasher = hashlib.new("sha256")
        hasher.update(row["prompt"].encode())
        input_ids = tokenizer.encode(row["prompt"]) + [tokenizer.eos_token_id]
        label_ids = input_ids.copy()
        return {"input_ids": input_ids, "labels": label_ids, "hash": hasher.hexdigest()}

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
        train_data.remove_columns(["hash"]),
        collate_fn=data_collator,
        batch_size=batch_size,
    )
    test_dataloader = torch.utils.data.DataLoader(
        test_data.remove_columns(["hash"]),
        collate_fn=data_collator,
        batch_size=batch_size,
    )

    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
    lr_scheduler = transformers.get_linear_schedule_with_warmup(
        optimizer=optimizer,
        num_warmup_steps=0,
        num_training_steps=len(train_dataloader) * num_epochs,
    )

    from peft import LoraConfig, TaskType, get_peft_model

    peft_config = LoraConfig(
        lora_alpha=alpha,
        lora_dropout=dropout,
        inference_mode=False,
        target_modules=["q_proj", "v_proj"],
        r=rank,
        bias="all",
        task_type=TaskType.CAUSAL_LM,
    )
    # model.add_adapter(peft_config)
    peft_model = get_peft_model(model, peft_config)
    peft_model.print_trainable_parameters()

    train_loss_idx = []
    train_loss_values = []
    test_loss_idx = []
    test_loss_values = []

    epoch_train_loss = []
    epoch_test_loss = []
    for epoch in range(num_epochs):
        model.train()
        train_loss = 0
        for step, batch in enumerate(tqdm.tqdm(train_dataloader)):
            outputs = model(**batch.to(device))
            loss = outputs.loss
            loss_step = loss.detach().cpu().float()

            train_loss_idx.append(train_data[step]["hash"])
            train_loss_values.append(loss_step.item())

            train_loss += loss_step
            if math.isnan(train_loss):
                print(tokenizer.decode(batch))
                print(loss_step)
                raise ValueError("training reach NaN")
            loss.backward()
            optimizer.step()
            lr_scheduler.step()
            optimizer.zero_grad()

            if step % 2000 == 1999:
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
            loss_step = loss.detach().cpu().float()

            test_loss_idx.append(test_data[step]["hash"])
            test_loss_values.append(loss_step.item())

            test_loss += loss_step

        test_epoch_loss = test_loss / len(test_dataloader)
        train_epoch_loss = train_loss / len(train_dataloader)
        print(f"{epoch=}: {train_epoch_loss=} {test_epoch_loss=}")

        epoch_train_loss.append(train_epoch_loss)
        epoch_test_loss.append((test_epoch_loss, epoch))

        peft_model.save_pretrained(str(out_dir / "checkpoints" / str(epoch)))

    train_series = pandas.Series(
        name="train-loss", data=train_loss_values, index=train_loss_idx
    )
    train_series.to_json(out_dir / "train-series.json", orient="split")

    test_series = pandas.Series(
        name="test-loss", data=test_loss_values, index=test_loss_idx
    )
    test_series.to_json(out_dir / "test-series.json", orient="split")

    sorted_epochs = sorted(epoch_test_loss)
    _, best_epoch = sorted_epochs[0]

    print("Results:")
    for j in range(num_epochs):
        print(f"{j}: train_loss={epoch_train_loss[j]} test_loss={epoch_test_loss[j]}")
    print(f"best epoch: {best_epoch}")
    if (out_dir / "final").exists():
        shutil.rmtree(out_dir / "final")
    shutil.copytree(out_dir / "checkpoints" / str(best_epoch), out_dir / "final")
