from __future__ import annotations

import datasets


class MultiSubsetLoader:
    def load_data(self, **kwargs):
        """Load dataset containing multiple subsets from HuggingFace hub"""
        if self.data_loaded:
            return

        fast_loading = self.fast_loading if hasattr(self, "fast_loading") else False
        if fast_loading:
            self.fast_load()
        else:
            self.slow_load()

        self.dataset_transform()
        self.data_loaded = True

    def fast_load(self, **kwargs):
        """Load all subsets at once, then group by language with Polars. Using fast loading has two requirements:
        - Each row in the dataset should have a 'lang' feature giving the corresponding language/language pair
        - The datasets must have a 'default' config that loads all the subsets of the dataset (see https://huggingface.co/docs/datasets/en/repository_structure#configurations)
        """
        self.dataset = {}
        merged_dataset = datasets.load_dataset(
            **self.metadata_dict["dataset"]
        )  # load "default" subset
        for split in self.metadata.eval_splits:
            grouped_by_lang = dict(merged_dataset[split].to_polars().group_by("lang"))
            for lang in self.langs:
                if lang not in self.dataset:
                    self.dataset[lang] = {}
                self.dataset[lang][split] = datasets.Dataset.from_polars(
                    grouped_by_lang[lang].drop("lang")
                )  # Remove lang column and convert back to HF datasets, not strictly necessary but better for compatibility

    def slow_load(self, **kwargs):
        """Load each subsets iteratively"""
        self.dataset = {}
        for lang in self.langs:
            self.dataset[lang] = datasets.load_dataset(
                name=lang,
                **self.metadata_dict.get("dataset", None),
            )
