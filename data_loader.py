"""
Data Loader Module for AI-Powered Requirements Engineering Tool
Handles loading, preprocessing, and validation of datasets
Datasets: Pure, PROMISE, Aerospace, REQuestA
"""

import os
import json
import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Any, Union
from sklearn.model_selection import train_test_split
from logger import get_logger
from config import AppConfig, RETaskType, DatasetConfig

logger = get_logger(__name__)


class DataLoader:
    """Base class for loading and preprocessing datasets"""

    def __init__(self, dataset_config: DatasetConfig):
        self.config = dataset_config
        self.data = None
        self.logger = get_logger(self.__class__.__name__)

    def load(self) -> Union[pd.DataFrame, Dict, List]:
        """Load dataset based on configuration"""
        raise NotImplementedError("Subclasses must implement load()")

    def preprocess(self) -> Union[pd.DataFrame, Dict, List]:
        """Preprocess loaded data"""
        raise NotImplementedError("Subclasses must implement preprocess()")

    def validate(self) -> bool:
        """Validate data integrity"""
        raise NotImplementedError("Subclasses must implement validate()")

    def get_split(self,
                  test_size: float = 0.2,
                  val_size: float = 0.1,
                  random_state: int = 42) -> Tuple:
        """Split data into train, validation, and test sets"""
        raise NotImplementedError("Subclasses must implement get_split()")


class PureDataLoader(DataLoader):
    """
    Pure Dataset Loader
    Used for Requirements Extraction task
    7,445 samples
    """

    def load(self) -> pd.DataFrame:
        """Load Pure dataset from CSV"""
        try:
            if not os.path.exists(self.config.path):
                self.logger.warning(f"Pure dataset not found at {self.config.path}")
                self.logger.info("Creating placeholder Pure dataset structure")
                return self._create_placeholder_dataframe()

            df = pd.read_csv(self.config.path)
            self.data = df
            self.logger.info(f"Loaded Pure dataset with {len(df)} samples")
            return df

        except Exception as e:
            self.logger.error(f"Error loading Pure dataset: {str(e)}")
            raise

    def _create_placeholder_dataframe(self) -> pd.DataFrame:
        """Create placeholder dataframe for Pure dataset"""
        placeholder_data = {
            'id': list(range(1, 101)),
            'source_text': [f'Sample requirement text {i}' for i in range(100)],
            'extracted_requirements': [f'Requirement {i}' for i in range(100)],
            'label': np.random.choice(['functional', 'non_functional'], 100)
        }
        return pd.DataFrame(placeholder_data)

    def preprocess(self) -> pd.DataFrame:
        """Preprocess Pure dataset"""
        if self.data is None:
            self.load()

        df = self.data.copy()

        # Remove duplicates
        df = df.drop_duplicates(subset=['source_text'], keep='first')

        # Handle missing values
        df = df.dropna(subset=['source_text'])

        # Text normalization
        df['source_text'] = df['source_text'].str.strip().str.lower()

        # Remove special characters if needed
        df['source_text'] = df['source_text'].str.replace(r'[^\w\s]', '', regex=True)

        self.logger.info(f"Preprocessed Pure dataset: {len(df)} samples after cleaning")
        self.data = df
        return df

    def validate(self) -> bool:
        """Validate Pure dataset"""
        if self.data is None:
            self.logger.error("No data loaded")
            return False

        required_columns = ['source_text']
        if not all(col in self.data.columns for col in required_columns):
            self.logger.error(f"Missing required columns: {required_columns}")
            return False

        if len(self.data) == 0:
            self.logger.error("Dataset is empty")
            return False

        self.logger.info("Pure dataset validation passed")
        return True

    def get_split(self,
                  test_size: float = 0.2,
                  val_size: float = 0.1,
                  random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Split Pure dataset"""
        if self.data is None:
            self.preprocess()

        # Split into train+val and test
        train_val, test = train_test_split(
            self.data,
            test_size=test_size,
            random_state=random_state
        )

        # Split train+val into train and val
        adjusted_val_size = val_size / (1 - test_size)
        train, val = train_test_split(
            train_val,
            test_size=adjusted_val_size,
            random_state=random_state
        )

        self.logger.info(f"Data split - Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")
        return train.reset_index(drop=True), val.reset_index(drop=True), test.reset_index(drop=True)


class PROMISEDataLoader(DataLoader):
    """
    PROMISE Dataset Loader
    Used for Requirements Classification task
    622 samples (Functional vs Non-functional)
    """

    def load(self) -> pd.DataFrame:
        """Load PROMISE dataset"""
        try:
            if not os.path.exists(self.config.path):
                self.logger.warning(f"PROMISE dataset not found at {self.config.path}")
                return self._create_placeholder_dataframe()

            df = pd.read_csv(self.config.path)
            self.data = df
            self.logger.info(f"Loaded PROMISE dataset with {len(df)} samples")
            return df

        except Exception as e:
            self.logger.error(f"Error loading PROMISE dataset: {str(e)}")
            raise

    def _create_placeholder_dataframe(self) -> pd.DataFrame:
        """Create placeholder dataframe for PROMISE dataset"""
        placeholder_data = {
            'id': list(range(1, 101)),
            'requirement_text': [f'Requirement {i}' for i in range(100)],
            'type': np.random.choice(['Functional', 'Non-Functional'], 100),
            'source': np.random.choice(['OpenStack', 'ALOJA', 'UBUNTU'], 100)
        }
        return pd.DataFrame(placeholder_data)

    def preprocess(self) -> pd.DataFrame:
        """Preprocess PROMISE dataset"""
        if self.data is None:
            self.load()

        df = self.data.copy()

        # Remove duplicates
        df = df.drop_duplicates(subset=['requirement_text'], keep='first')

        # Handle missing values
        df = df.dropna(subset=['requirement_text', 'type'])

        # Normalize text
        df['requirement_text'] = df['requirement_text'].str.strip().str.lower()

        # Standardize class labels
        if 'type' in df.columns:
            df['type'] = df['type'].str.lower().replace({
                'functional': 'functional',
                'non-functional': 'non_functional',
                'non_functional': 'non_functional'
            })

        self.logger.info(f"Preprocessed PROMISE dataset: {len(df)} samples")
        self.data = df
        return df

    def validate(self) -> bool:
        """Validate PROMISE dataset"""
        if self.data is None:
            self.logger.error("No data loaded")
            return False

        required_columns = ['requirement_text', 'type']
        if not all(col in self.data.columns for col in required_columns):
            self.logger.error(f"Missing required columns: {required_columns}")
            return False

        valid_types = ['functional', 'non_functional']
        if not self.data['type'].isin(valid_types).all():
            self.logger.error(f"Invalid type values. Expected: {valid_types}")
            return False

        self.logger.info("PROMISE dataset validation passed")
        return True

    def get_split(self,
                  test_size: float = 0.2,
                  val_size: float = 0.1,
                  random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Split PROMISE dataset with stratification"""
        if self.data is None:
            self.preprocess()

        # Stratified split
        train_val, test = train_test_split(
            self.data,
            test_size=test_size,
            random_state=random_state,
            stratify=self.data['type']
        )

        adjusted_val_size = val_size / (1 - test_size)
        train, val = train_test_split(
            train_val,
            test_size=adjusted_val_size,
            random_state=random_state,
            stratify=train_val['type']
        )

        self.logger.info(f"Data split - Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")
        return train.reset_index(drop=True), val.reset_index(drop=True), test.reset_index(drop=True)


class AerospaceDataLoader(DataLoader):
    """
    Aerospace Dataset Loader
    Used for Named Entity Recognition (NER) task
    6,347 words
    """

    def load(self) -> List[Dict[str, Any]]:
        """Load Aerospace NER dataset"""
        try:
            if not os.path.exists(self.config.path):
                self.logger.warning(f"Aerospace dataset not found at {self.config.path}")
                return self._create_placeholder_data()

            with open(self.config.path, 'r') as f:
                self.data = json.load(f)

            self.logger.info(f"Loaded Aerospace dataset with {len(self.data)} samples")
            return self.data

        except Exception as e:
            self.logger.error(f"Error loading Aerospace dataset: {str(e)}")
            raise

    def _create_placeholder_data(self) -> List[Dict[str, Any]]:
        """Create placeholder data for Aerospace dataset"""
        placeholder_data = [
            {
                'id': i,
                'text': f'Aerospace requirement {i}',
                'entities': [
                    {'start': 0, 'end': 8, 'label': 'ENTITY_TYPE', 'text': 'Aerospace'}
                ]
            }
            for i in range(100)
        ]
        return placeholder_data

    def preprocess(self) -> List[Dict[str, Any]]:
        """Preprocess Aerospace dataset"""
        if self.data is None:
            self.load()

        processed_data = []
        for item in self.data:
            if 'text' in item and item['text'].strip():
                # Normalize text
                item['text'] = item['text'].strip().lower()
                # Validate entities
                if 'entities' in item and isinstance(item['entities'], list):
                    processed_data.append(item)

        self.logger.info(f"Preprocessed Aerospace dataset: {len(processed_data)} valid samples")
        self.data = processed_data
        return processed_data

    def validate(self) -> bool:
        """Validate Aerospace dataset"""
        if self.data is None or len(self.data) == 0:
            self.logger.error("No data loaded")
            return False

        for item in self.data:
            if 'text' not in item or 'entities' not in item:
                self.logger.error("Missing required fields in Aerospace dataset")
                return False

        self.logger.info("Aerospace dataset validation passed")
        return True

    def get_split(self,
                  test_size: float = 0.2,
                  val_size: float = 0.1,
                  random_state: int = 42) -> Tuple[List, List, List]:
        """Split Aerospace dataset"""
        if self.data is None:
            self.preprocess()

        np.random.seed(random_state)
        indices = np.arange(len(self.data))
        np.random.shuffle(indices)

        test_idx = int(len(self.data) * test_size)
        val_idx = int(len(self.data) * (test_size + val_size))

        test_data = [self.data[i] for i in indices[:test_idx]]
        val_data = [self.data[i] for i in indices[test_idx:val_idx]]
        train_data = [self.data[i] for i in indices[val_idx:]]

        self.logger.info(f"Data split - Train: {len(train_data)}, Val: {len(val_data)}, Test: {len(test_data)}")
        return train_data, val_data, test_data


class REQuestADataLoader(DataLoader):
    """
    REQuestA Dataset Loader
    Used for Question Answering task
    300 QA pairs
    """

    def load(self) -> List[Dict[str, str]]:
        """Load REQuestA dataset"""
        try:
            if not os.path.exists(self.config.path):
                self.logger.warning(f"REQuestA dataset not found at {self.config.path}")
                return self._create_placeholder_data()

            with open(self.config.path, 'r') as f:
                self.data = json.load(f)

            self.logger.info(f"Loaded REQuestA dataset with {len(self.data)} QA pairs")
            return self.data

        except Exception as e:
            self.logger.error(f"Error loading REQuestA dataset: {str(e)}")
            raise

    def _create_placeholder_data(self) -> List[Dict[str, str]]:
        """Create placeholder data for REQuestA dataset"""
        placeholder_data = [
            {
                'id': i,
                'requirement': f'Requirement description {i}',
                'question': f'What is the requirement {i}?',
                'answer': f'This is the answer to requirement {i}'
            }
            for i in range(100)
        ]
        return placeholder_data

    def preprocess(self) -> List[Dict[str, str]]:
        """Preprocess REQuestA dataset"""
        if self.data is None:
            self.load()

        processed_data = []
        for item in self.data:
            # Validate required fields
            if all(key in item for key in ['requirement', 'question', 'answer']):
                # Normalize text
                item['requirement'] = item['requirement'].strip().lower()
                item['question'] = item['question'].strip().lower()
                item['answer'] = item['answer'].strip().lower()
                processed_data.append(item)

        self.logger.info(f"Preprocessed REQuestA dataset: {len(processed_data)} valid QA pairs")
        self.data = processed_data
        return processed_data

    def validate(self) -> bool:
        """Validate REQuestA dataset"""
        if self.data is None or len(self.data) == 0:
            self.logger.error("No data loaded")
            return False

        required_fields = ['requirement', 'question', 'answer']
        for item in self.data:
            if not all(field in item for field in required_fields):
                self.logger.error("Missing required fields in REQuestA dataset")
                return False

        self.logger.info("REQuestA dataset validation passed")
        return True

    def get_split(self,
                  test_size: float = 0.2,
                  val_size: float = 0.1,
                  random_state: int = 42) -> Tuple[List, List, List]:
        """Split REQuestA dataset"""
        if self.data is None:
            self.preprocess()

        np.random.seed(random_state)
        indices = np.arange(len(self.data))
        np.random.shuffle(indices)

        test_idx = int(len(self.data) * test_size)
        val_idx = int(len(self.data) * (test_size + val_size))

        test_data = [self.data[i] for i in indices[:test_idx]]
        val_data = [self.data[i] for i in indices[test_idx:val_idx]]
        train_data = [self.data[i] for i in indices[val_idx:]]

        self.logger.info(f"Data split - Train: {len(train_data)}, Val: {len(val_data)}, Test: {len(test_data)}")
        return train_data, val_data, test_data


class DataLoaderFactory:
    """Factory for creating appropriate data loaders"""

    _loaders = {
        RETaskType.EXTRACTION: PureDataLoader,
        RETaskType.CLASSIFICATION: PROMISEDataLoader,
        RETaskType.NER: AerospaceDataLoader,
        RETaskType.QA: REQuestADataLoader,
    }

    @staticmethod
    def create_loader(dataset_config: DatasetConfig) -> DataLoader:
        """Create appropriate loader based on task type"""
        loader_class = DataLoaderFactory._loaders.get(dataset_config.task_type)
        if loader_class is None:
            raise ValueError(f"No loader for task type: {dataset_config.task_type}")
        return loader_class(dataset_config)

    @staticmethod
    def load_and_prepare(dataset_config: DatasetConfig) -> Tuple:
        """Load, preprocess, validate, and split dataset"""
        loader = DataLoaderFactory.create_loader(dataset_config)
        loader.load()
        loader.preprocess()

        if not loader.validate():
            raise ValueError(f"Dataset validation failed: {dataset_config.name}")

        return loader.get_split()
