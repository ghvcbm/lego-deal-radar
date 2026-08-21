import unittest
from unittest.mock import Mock, patch

from python_project.bot import handle_update
from python_project.cli import build_parser, main
from python_project.config import ConfigurationError, required_env
from python_project.database import ArchitectureSet, connect, list_architecture_sets, replace_architecture_sets
from python_project.rebrickable import RebrickableClient
from python_project.telegram import format_architecture_sets


class ConfigurationTests(unittest.TestCase):
    def test_required_env_rejects_missing_values(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(ConfigurationError):
                required_env("EXAMPLE_API_KEY")


class CLIParsingTests(unittest.TestCase):
    def test_lookup_command_accepts_set_number(self) -> None:
        args = build_parser().parse_args(["lookup-set", "75192-1"])
        self.assertEqual(args.set_number, "75192-1")

    def test_send_message_command_accepts_chat_and_text(self) -> None:
        args = build_parser().parse_args(["send-message", "123", "Hello"])
        self.assertEqual((args.chat_id, args.text), ("123", "Hello"))

    @patch("python_project.cli.RebrickableClient")
    def test_lookup_prints_api_result(self, client_class) -> None:
        client_class.return_value.get_set.return_value = {"set_num": "architecture-set"}
        self.assertEqual(main(["lookup-set", "architecture-set"]), 0)
        client_class.return_value.get_set.assert_called_once_with("architecture-set")


class RebrickableTests(unittest.TestCase):
    def test_exact_theme_is_selected_and_set_pages_are_combined(self) -> None:
        client = RebrickableClient(api_key="test-key")
        responses = iter(
            [
                {
                    "results": [
                        {"id": 1, "name": "Architecture"},
                        {"id": 2, "name": "Architecture: Other"},
                    ],
                    "next": None,
                },
                {
                    "results": [{"set_num": "first", "name": "First"}],
                    "next": "next-page",
                },
                {
                    "results": [{"set_num": "second", "name": "Second"}],
                    "next": None,
                },
            ]
        )
        with patch.object(client, "_get", side_effect=lambda *args, **kwargs: next(responses)):
            sets = client.get_architecture_sets()
        self.assertEqual([item["set_num"] for item in sets], ["first", "second"])


class DatabaseAndBotTests(unittest.TestCase):
    def test_sets_are_stored_and_sorted(self) -> None:
        connection = connect(":memory:")
        try:
            replace_architecture_sets(
                connection,
                [
                    ArchitectureSet("new", "New", 2024, 100),
                    ArchitectureSet("old", "Old", 2020, 50),
                ],
            )
            self.assertEqual(
                [item.set_num for item in list_architecture_sets(connection)],
                ["new", "old"],
            )
        finally:
            connection.close()

    def test_architecture_messages_include_count_and_fields(self) -> None:
        messages = format_architecture_sets(
            [ArchitectureSet("set", "A building", 2024, 123)]
        )
        self.assertEqual(messages, ["LEGO Architecture: 1 sets\nset — A building (2024, 123 parts)"])

    def test_start_command_sends_welcome(self) -> None:
        bot = Mock()
        handle_update(
            bot,
            {"message": {"text": "/start", "chat": {"id": 42}}},
        )
        bot.send_message.assert_called_once()
        self.assertIn("Welcome", bot.send_message.call_args.args[1])