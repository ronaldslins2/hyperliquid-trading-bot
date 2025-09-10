"""
Private Key Manager

Unified, secure private key management with support for:
- Different keys for testnet vs mainnet
- Per-bot instance key configuration
- File-based and environment-based keys
- Fallback strategies
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging


class KeyManager:
    """
    Unified private key management

    Priority order for key resolution:
    1. Bot-specific config override
    2. Environment-specific keys (testnet/mainnet)
    3. Legacy single key (for backward compatibility)
    4. File-based keys (environment-specific)
    5. Legacy single key file
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_private_key(
        self, testnet: bool, bot_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Get private key for the specified environment and bot configuration

        Args:
            testnet: True for testnet, False for mainnet
            bot_config: Optional bot-specific configuration

        Returns:
            Private key string

        Raises:
            ValueError: If no private key can be found
        """

        network = "testnet" if testnet else "mainnet"

        # 1. Check for bot-specific key override
        if bot_config:
            bot_key = self._get_bot_specific_key(bot_config, testnet)
            if bot_key:
                self.logger.debug(f"Using bot-specific private key for {network}")
                return bot_key

        # 2. Check for environment-specific keys
        env_key = self._get_environment_specific_key(testnet)
        if env_key:
            self.logger.debug(f"Using environment-specific private key for {network}")
            return env_key

        # 3. Check for legacy single key (backward compatibility)
        legacy_key = self._get_legacy_key()
        if legacy_key:
            self.logger.warning(
                f"Using legacy single private key for {network} - consider using environment-specific keys"
            )
            return legacy_key

        # 4. Check for file-based keys
        file_key = self._get_file_based_key(testnet)
        if file_key:
            self.logger.debug(f"Using file-based private key for {network}")
            return file_key

        # 5. Check for legacy single key file
        legacy_file_key = self._get_legacy_file_key()
        if legacy_file_key:
            self.logger.warning(
                f"Using legacy key file for {network} - consider using environment-specific key files"
            )
            return legacy_file_key

        # No key found
        raise ValueError(
            f"No private key found for {network}. Please set one of:\n"
            f"- HYPERLIQUID_{'TESTNET' if testnet else 'MAINNET'}_PRIVATE_KEY\n"
            f"- HYPERLIQUID_{'TESTNET' if testnet else 'MAINNET'}_KEY_FILE\n"
            f"- HYPERLIQUID_PRIVATE_KEY (legacy)\n"
            f"- Or configure in bot config file"
        )

    def _get_bot_specific_key(
        self, bot_config: Dict[str, Any], testnet: bool
    ) -> Optional[str]:
        """Get bot-specific private key override"""

        # Check for direct key in bot config (not recommended, but supported)
        if testnet and "testnet_private_key" in bot_config:
            return bot_config["testnet_private_key"]
        elif not testnet and "mainnet_private_key" in bot_config:
            return bot_config["mainnet_private_key"]
        elif "private_key" in bot_config:
            return bot_config["private_key"]

        # Check for key file in bot config
        key_file_key = "testnet_key_file" if testnet else "mainnet_key_file"
        if key_file_key in bot_config:
            return self._read_key_file(bot_config[key_file_key])
        elif "private_key_file" in bot_config:
            return self._read_key_file(bot_config["private_key_file"])

        return None

    def _get_environment_specific_key(self, testnet: bool) -> Optional[str]:
        """Get environment-specific private key"""

        env_var = (
            "HYPERLIQUID_TESTNET_PRIVATE_KEY"
            if testnet
            else "HYPERLIQUID_MAINNET_PRIVATE_KEY"
        )
        return os.getenv(env_var)

    def _get_legacy_key(self) -> Optional[str]:
        """Get legacy single private key"""
        return os.getenv("HYPERLIQUID_PRIVATE_KEY")

    def _get_file_based_key(self, testnet: bool) -> Optional[str]:
        """Get private key from environment-specific file"""

        env_var = (
            "HYPERLIQUID_TESTNET_KEY_FILE"
            if testnet
            else "HYPERLIQUID_MAINNET_KEY_FILE"
        )
        key_file = os.getenv(env_var)

        if key_file:
            return self._read_key_file(key_file)

        return None

    def _get_legacy_file_key(self) -> Optional[str]:
        """Get private key from legacy single key file"""

        key_file = os.getenv("HYPERLIQUID_PRIVATE_KEY_FILE")
        if key_file:
            return self._read_key_file(key_file)

        return None

    def _read_key_file(self, file_path: str) -> Optional[str]:
        """Read private key from file"""

        try:
            key_path = Path(file_path)

            if not key_path.exists():
                self.logger.warning(f"Private key file not found: {file_path}")
                return None

            # Read and clean the key
            with open(key_path, "r") as f:
                private_key = f.read().strip()

            # Validate format
            if not private_key.startswith("0x"):
                private_key = "0x" + private_key

            if len(private_key) != 66:  # 0x + 64 hex chars
                self.logger.warning(f"Invalid private key format in {file_path}")
                return None

            return private_key

        except Exception as e:
            self.logger.error(f"Failed to read private key from {file_path}: {e}")
            return None

    def get_key_info(
        self, testnet: bool, bot_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get information about which key source will be used"""

        network = "testnet" if testnet else "mainnet"
        info = {
            "network": network,
            "key_source": None,
            "key_found": False,
            "warnings": [],
        }

        try:
            # Try to get key and track source
            if bot_config:
                bot_key = self._get_bot_specific_key(bot_config, testnet)
                if bot_key:
                    info.update({"key_source": "bot_config", "key_found": True})
                    return info

            env_key = self._get_environment_specific_key(testnet)
            if env_key:
                info.update({"key_source": f"environment_{network}", "key_found": True})
                return info

            legacy_key = self._get_legacy_key()
            if legacy_key:
                info.update(
                    {
                        "key_source": "legacy_environment",
                        "key_found": True,
                        "warnings": [
                            "Using legacy single private key - consider environment-specific keys"
                        ],
                    }
                )
                return info

            file_key = self._get_file_based_key(testnet)
            if file_key:
                info.update({"key_source": f"file_{network}", "key_found": True})
                return info

            legacy_file_key = self._get_legacy_file_key()
            if legacy_file_key:
                info.update(
                    {
                        "key_source": "legacy_file",
                        "key_found": True,
                        "warnings": [
                            "Using legacy key file - consider environment-specific key files"
                        ],
                    }
                )
                return info

            info["key_source"] = "none"
            return info

        except Exception as e:
            info["error"] = str(e)
            return info


# Global key manager instance
key_manager = KeyManager()
