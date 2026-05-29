"""Generate project ERD (PNG + SVG) via django-extensions graph_models."""

import shutil
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError


PROJECT_APPS = ("accounts", "chat", "onboarding")

EXCLUDED_MODELS = (
    "Session",
    "ContentType",
    "LogEntry",
    "Group",
    "Permission",
    "AdminLogEntry",
    # Shown on CustomUser as <AbstractBaseUser, PermissionsMixin>; omit duplicate nodes.
    "AbstractBaseUser",
    "PermissionsMixin",
)


class Command(BaseCommand):
    """Render database schema diagrams for project apps only."""

    help = (
        "Generate ERD as PNG and SVG (django-extensions graph_models + Graphviz). "
        "Includes model fields; excludes Django contrib noise."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-dir",
            default="DB Diagram",
            help="Directory for erd.png, erd.svg, and erd.dot.",
        )
        parser.add_argument(
            "--dot-only",
            action="store_true",
            help="Write erd.dot only; skip PNG/SVG rendering.",
        )

    def handle(self, *args, **options):
        output_dir = Path(options["output_dir"])
        if not output_dir.is_absolute():
            output_dir = settings.BASE_DIR / output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        dot_path = output_dir / "erd.dot"
        png_path = output_dir / "erd.png"
        svg_path = output_dir / "erd.svg"

        common = {
            "exclude_models": ",".join(EXCLUDED_MODELS),
            "theme": "django2018",
            "layout": "dot",
            "rankdir": "TB",
            "verbosity": options["verbosity"],
        }

        self.stdout.write("Generating DOT from Django models…")
        call_command(
            "graph_models",
            *PROJECT_APPS,
            dot=True,
            outputfile=str(dot_path),
            **common,
        )

        if not dot_path.is_file():
            raise CommandError(f"graph_models did not create {dot_path}")

        self.stdout.write(self.style.SUCCESS(f"Wrote {dot_path}"))

        if options["dot_only"]:
            return

        self._render_with_dot(dot_path, png_path, "png")
        self._render_with_dot(dot_path, svg_path, "svg")

        self.stdout.write(self.style.SUCCESS(f"Wrote {png_path}"))
        self.stdout.write(self.style.SUCCESS(f"Wrote {svg_path}"))

    def _render_with_dot(self, dot_path: Path, out_path: Path, fmt: str) -> None:
        dot_bin = shutil.which("dot")
        if dot_bin:
            subprocess.run(
                [dot_bin, f"-T{fmt}", str(dot_path), "-o", str(out_path)],
                check=True,
            )
            return

        self.stdout.write(
            self.style.WARNING("`dot` not found on PATH; using graph_models/pydot…")
        )
        call_command(
            "graph_models",
            *PROJECT_APPS,
            outputfile=str(out_path),
            exclude_models=",".join(EXCLUDED_MODELS),
            theme="django2018",
            layout="dot",
            rankdir="TB",
            verbosity=0,
        )
