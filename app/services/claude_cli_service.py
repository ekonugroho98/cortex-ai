"""
Claude Code CLI Service
Handles subprocess communication with Claude Code CLI
"""
import asyncio
import json
import os
import tempfile
from typing import Optional, Dict, Any
from pathlib import Path
from loguru import logger
import shutil

from app.config import settings


class ClaudeCLIService:
    """
    Service for interacting with Claude Code CLI via subprocess
    """

    def __init__(self):
        """Initialize Claude CLI service"""
        self.claude_executable = shutil.which("claude")
        if not self.claude_executable:
            logger.warning("Claude Code CLI not found in PATH")

        # Workspace directory for Claude CLI
        self.workspace_path = Path(settings.claude_workspace_path)
        self.workspace_path.mkdir(parents=True, exist_ok=True)

        # Claude settings directory
        self.claude_settings_dir = Path.home() / ".claude"

        logger.info(f"Claude CLI workspace: {self.workspace_path}")

    def is_available(self) -> bool:
        """Check if Claude CLI is available"""
        return self.claude_executable is not None

    def setup_workspace(self, bigquery_context: Dict[str, Any]) -> str:
        """
        Setup Claude workspace with BigQuery context

        Creates necessary files and configuration for Claude CLI

        Args:
            bigquery_context: BigQuery schema and context information

        Returns:
            Path to workspace directory
        """
        try:
            # Create workspace structure
            workspace = self.workspace_path / "bigquery_context"
            workspace.mkdir(parents=True, exist_ok=True)

            # Write BigQuery schema documentation
            schema_md = workspace / "schemas.md"
            with open(schema_md, "w") as f:
                f.write(self._generate_schema_doc(bigquery_context))

            # Write query examples
            examples_md = workspace / "examples.md"
            with open(examples_md, "w") as f:
                f.write(self._generate_examples_doc())

            # Write SQL conventions
            conventions_md = workspace / "conventions.md"
            with open(conventions_md, "w") as f:
                f.write(self._generate_conventions_doc())

            # Create .claude/settings.json in workspace
            claude_settings = workspace / ".claude"
            claude_settings.mkdir(exist_ok=True)

            settings_file = claude_settings / "settings.json"
            with open(settings_file, "w") as f:
                json.dump({
                    "env": {
                        "ANTHROPIC_DEFAULT_HAIKU_MODEL": "glm-4.5-air",
                        "ANTHROPIC_DEFAULT_SONNET_MODEL": "glm-4.7",
                        "ANTHROPIC_DEFAULT_OPUS_MODEL": "glm-4.7"
                    }
                }, f, indent=2)

            logger.info(f"Workspace setup complete: {workspace}")
            return str(workspace)

        except Exception as e:
            logger.error(f"Failed to setup workspace: {e}")
            raise

    def _generate_schema_doc(self, context: Dict[str, Any]) -> str:
        """Generate BigQuery schema documentation"""
        doc = "# BigQuery Schema Documentation\n\n"

        doc += f"**Project ID**: {context.get('project_id', 'N/A')}\n\n"
        doc += f"**Location**: {context.get('location', 'US')}\n\n"

        if "datasets" in context:
            doc += "## Datasets and Tables\n\n"
            for dataset in context["datasets"]:
                doc += f"### {dataset['dataset_id']}\n\n"
                doc += f"- Location: {dataset.get('location', 'N/A')}\n"
                doc += f"- Tables: {dataset.get('tables_count', 0)}\n\n"

                if "tables" in dataset:
                    for table in dataset["tables"]:
                        doc += f"#### {table['table_id']}\n\n"
                        doc += f"- Type: {table.get('table_type', 'TABLE')}\n"
                        doc += f"- Full reference: `{table['full_table_id']}`\n"

                        if "schema" in table:
                            doc += "\n**Columns**:\n\n"
                            doc += "| Column | Type | Mode | Description |\n"
                            doc += "|--------|------|------|-------------|\n"
                            for col in table["schema"]:
                                desc = col.get('description', '-')
                                doc += f"| {col['name']} | {col['type']} | {col['mode']} | {desc} |\n"
                        doc += "\n"

        return doc

    def _generate_examples_doc(self) -> str:
        """Generate query examples documentation"""
        return """# BigQuery Query Examples

## Basic Queries

### Select with limit
```sql
SELECT *
FROM `project.dataset.table`
LIMIT 100
```

### Count records
```sql
SELECT COUNT(*) as total_count
FROM `project.dataset.table`
```

### Filter with WHERE clause
```sql
SELECT column1, column2
FROM `project.dataset.table`
WHERE date >= '2024-01-01'
  AND status = 'active'
```

### Group by and aggregate
```sql
SELECT
  category,
  COUNT(*) as count,
  SUM(amount) as total_amount
FROM `project.dataset.table`
GROUP BY category
ORDER BY total_amount DESC
```

### Join tables
```sql
SELECT
  t1.user_id,
  t1.email,
  t2.order_count
FROM `project.dataset.users` t1
INNER JOIN `project.dataset.orders` t2
  ON t1.user_id = t2.user_id
```

### Window functions
```sql
SELECT
  user_id,
  order_date,
  amount,
  SUM(amount) OVER (
    PARTITION BY user_id
    ORDER BY order_date
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) as running_total
FROM `project.dataset.orders`
```

## Best Practices

1. **Always use fully qualified table names**: `project.dataset.table`
2. **Use LIMIT clause** for development/testing
3. **Partition your tables** on date/timestamp columns for better performance
4. **Use _PARTITIONDATE** pseudo-column for partition pruning
5. **Avoid SELECT *** in production - list specific columns
6. **Use ARRAY and STRUCT types** for nested/repeated data
"""

    def _generate_conventions_doc(self) -> str:
        """Generate SQL conventions documentation"""
        return """# SQL Conventions for BigQuery

## Naming Conventions

- Table names: lowercase_with_underscores
- Column names: lowercase_with_underscores
- Use descriptive names: `user_created_at` not `uat`

## Query Formatting

```sql
SELECT
  user_id,
  user_email,
  created_at
FROM `my-project.analytics.users`
WHERE status = 'active'
  AND created_at >= '2024-01-01'
ORDER BY created_at DESC
LIMIT 100
```

## BigQuery Specific Features

### Use ARRAY_AGG for aggregation
```sql
SELECT
  user_id,
  ARRAY_AGG(order_id IGNORE NULLS) as orders
FROM `project.dataset.orders`
GROUP BY user_id
```

### Use STRUCT for nested data
```sql
SELECT
  user_id,
  STRUCT(
    email as email,
    phone as phone
  ) as contact_info
FROM `project.dataset.users`
```

### Partitioning
```sql
-- Query specific partition
SELECT *
FROM `project.dataset.table`
WHERE _PARTITIONDATE = '2024-01-15'
```

## Performance Tips

1. **Filter early** - Use WHERE clause before JOIN
2. **Use partitioning** on date/timestamp columns
3. **Avoid CROSS JOIN** unless necessary
4. **Use materialized views** for repeated queries
5. **Cache results** with `use_query_cache=true`
"""

    async def execute_prompt(
        self,
        prompt: str,
        bigquery_context: Optional[Dict[str, Any]] = None,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Execute a prompt via Claude Code CLI subprocess

        Args:
            prompt: The prompt to send to Claude CLI
            bigquery_context: BigQuery schema context
            timeout: Timeout in seconds

        Returns:
            Response from Claude CLI with extracted content
        """
        if not self.is_available():
            raise RuntimeError("Claude Code CLI is not available")

        # Setup workspace with context
        if bigquery_context:
            workspace = self.setup_workspace(bigquery_context)
        else:
            workspace = str(self.workspace_path)

        # Construct full prompt with BigQuery context
        full_prompt = self._construct_prompt(prompt, bigquery_context)

        logger.info(f"Executing prompt via Claude CLI (timeout: {timeout}s)")

        try:
            # Create temporary script to capture output
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.sh',
                delete=False
            ) as script_file:
                script_path = script_file.name

                # Write bash script that calls claude
                script_content = f"""#!/bin/bash
cd "{workspace}"
echo "{full_prompt}" | claude --print 2>&1
"""
                script_file.write(script_content)
                script_file.flush()

            # Make script executable
            os.chmod(script_path, 0o755)

            # Execute the script
            process = await asyncio.create_subprocess_exec(
                script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workspace
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )

                output = stdout.decode('utf-8')
                error = stderr.decode('utf-8')

                logger.info(f"Claude CLI process completed with code: {process.returncode}")

                if process.returncode != 0:
                    logger.error(f"Claude CLI error: {error}")
                    raise RuntimeError(f"Claude CLI failed: {error}")

                # Parse output to extract relevant content
                result = self._parse_output(output)

                return {
                    "success": True,
                    "raw_output": output,
                    "parsed_content": result,
                    "workspace": workspace
                }

            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise TimeoutError(f"Claude CLI execution timed out after {timeout}s")

        except Exception as e:
            logger.error(f"Failed to execute Claude CLI: {e}")
            raise

    def _construct_prompt(
        self,
        user_prompt: str,
        bigquery_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Construct the full prompt with context and instructions

        Args:
            user_prompt: The user's prompt
            bigquery_context: BigQuery schema context

        Returns:
            Full prompt string
        """
        prompt_parts = []

        # Add system instruction
        prompt_parts.append("""You are a BigQuery SQL expert. Your task is to help users generate optimized BigQuery SQL queries based on their natural language requests.

IMPORTANT INSTRUCTIONS:
1. Always use fully qualified table names: `project.dataset.table`
2. Generate ONLY the SQL query wrapped in ```sql``` code block
3. Keep queries simple and performant
4. Add comments for complex logic
5. Output the SQL query only, no explanations needed""")

        # Add context about available schemas
        if bigquery_context:
            prompt_parts.append("\n\nAvailable BigQuery Resources:")

            if "datasets" in bigquery_context:
                for dataset in bigquery_context["datasets"]:
                    prompt_parts.append(f"\n- Dataset: {dataset['dataset_id']}")
                    if "tables" in dataset:
                        for table in dataset["tables"]:
                            prompt_parts.append(f"  - Table: {table['full_table_id']}")
                            if "schema" in table:
                                # Show ALL columns, not just first 5
                                cols = ", ".join([f"{col['name']} ({col['type']})" for col in table["schema"]])
                                prompt_parts.append(f"    Columns: {cols}")

        # Add user prompt
        prompt_parts.append(f"\n\nUser Request:\n{user_prompt}")

        # Add expected output format
        prompt_parts.append("\n\nExpected Output Format:")
        prompt_parts.append("""```sql
SELECT ...
FROM `project.dataset.table`
...
```""")

        return "\n".join(prompt_parts)

    def _parse_output(self, output: str) -> Dict[str, Any]:
        """
        Parse Claude CLI output to extract structured content

        Args:
            output: Raw output from Claude CLI

        Returns:
            Parsed content dictionary
        """
        result = {
            "text": output,
            "sql_query": None,
            "code_blocks": [],
            "reasoning": []
        }

        # Extract SQL code blocks
        import re
        sql_pattern = r'```sql\n(.*?)\n```'
        sql_matches = re.findall(sql_pattern, output, re.DOTALL)

        if sql_matches:
            result["sql_query"] = sql_matches[0].strip()
            result["code_blocks"] = sql_matches

        # Extract all code blocks
        code_pattern = r'```(\w*)\n(.*?)\n```'
        code_matches = re.findall(code_pattern, output, re.DOTALL)
        result["code_blocks"] = [{"lang": lang, "code": code} for lang, code in code_matches]

        return result


# Global service instance
claude_cli_service = ClaudeCLIService()
