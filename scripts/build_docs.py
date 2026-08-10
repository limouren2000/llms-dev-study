from __future__ import annotations

import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "_web"
GITHUB_REPO = "https://github.com/limouren2000/llms-dev-study"


def write_page(path: Path, content: str) -> None:
    """Write one generated website page."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def stage_markdown(
    source: Path,
    destination: Path,
    fallback_title: str | None = None,
) -> None:
    """Copy Markdown into the staging tree without changing the source."""
    if not source.exists():
        raise FileNotFoundError(f"Missing Markdown source: {source}")

    content = source.read_text(encoding="utf-8")

    # Some existing notes start at H2. Add an H1 only to the staged copy so
    # MkDocs gets a proper page title while the repository source stays intact.
    if fallback_title and not re.search(r"^#\s+.+$", content, re.MULTILINE):
        content = f"# {fallback_title}\n\n{content.lstrip()}"

    write_page(destination, content)


def copy_images(source_directory: Path, destination_directory: Path) -> None:
    """Copy images referenced by a staged README while preserving filenames."""
    destination_directory.mkdir(parents=True, exist_ok=True)

    for suffix in ("*.png", "*.jpg", "*.jpeg", "*.gif", "*.webp", "*.svg"):
        for source in source_directory.glob(suffix):
            shutil.copy2(source, destination_directory / source.name)


def extract_readme_section(
    start_pattern: str,
    end_pattern: str,
    title: str,
) -> str:
    """Extract one section from the root README and promote it to a page."""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    start = re.search(start_pattern, readme, re.MULTILINE)

    if start is None:
        raise ValueError(f"README.md is missing section: {start_pattern}")

    end = re.search(end_pattern, readme[start.end() :], re.MULTILINE)

    if end is None:
        raise ValueError(f"README.md is missing section boundary: {end_pattern}")

    end_position = start.end() + end.start()
    section = readme[start.start() : end_position]
    section = re.sub(
        start_pattern,
        f"# {title}",
        section,
        count=1,
        flags=re.MULTILINE,
    )
    section = re.sub(
        r"^(#{3,})",
        lambda match: match.group(1)[1:],
        section,
        flags=re.MULTILINE,
    )

    return section


def demote_headings(markdown: str) -> str:
    """Move headings down one level before embedding a README in a page."""
    return re.sub(
        r"^(#{1,5})([ \t]+)",
        lambda match: f"{match.group(1)}#{match.group(2)}",
        markdown,
        flags=re.MULTILINE,
    )


def build_home() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    rag_heading = re.search(r"^#\s+✅\s*RAG\s*$", readme, re.MULTILINE)

    if rag_heading is None:
        raise ValueError("README.md is missing the '# ✅ RAG' section marker")

    # The website home mirrors the repository README from the beginning up to,
    # but not including, the RAG section. Repository links are rewritten to
    # their website equivalents only in the generated staging copy.
    homepage = readme[: rag_heading.start()]
    website_links = {
        f"{GITHUB_REPO}/tree/main/0.LLM-Dev%20Study%20Router": "roadmap/index.md",
        f"{GITHUB_REPO}/tree/main/1.RAG": "rag/index.md",
        f"{GITHUB_REPO}/tree/main/2.Agent": "agent/index.md",
        f"{GITHUB_REPO}/tree/main/3.Interview": "interview/index.md",
        f"{GITHUB_REPO}/tree/main/4.Paper-read": "paper-read/index.md",
    }

    for repository_link, website_link in website_links.items():
        homepage = homepage.replace(repository_link, website_link)

    write_page(WEB / "index.md", homepage)


def build_roadmap() -> None:
    stage_markdown(
        ROOT / "0.LLM-Dev Study Router" / "README.md",
        WEB / "roadmap" / "index.md",
        "大模型应用开发学习路线",
    )


def build_rag() -> None:
    introduction = extract_readme_section(
        r"^#\s+✅\s*RAG\s*$",
        r"^##\s+llms-1\s*$",
        "RAG 学习路线",
    )
    content = f"""{introduction}
!!! tip "学习建议"

    llms-1 和 llms-2 用于快速建立对 RAG 和 AI 应用开发的整体认知，有个印象即可，不需要逐行过代码或纠结具体实现。学习重点放在后面的系统课程和入门项目。

## 学习内容

- [llms-1：RAG 扫盲课程](llms-1/index.md)
- [llms-2：RAG 检索课程](llms-2/index.md)
- [llms-3：RAG From Scratch](llms-3/index.md)
- [llms-4：RAG 入门项目](starter-project/index.md)

!!! note "关于 Notebook 和 PDF"

    Notebook、课程 PPT 和论文 PDF 保留在 GitHub 仓库中，不复制到文档网站。
    这样可以减小网站体积，同时继续保留原始学习资料。
"""

    write_page(WEB / "rag" / "index.md", content)

    pages = (
        (
            r"^##\s+llms-1\s*$",
            r"^##\s+llms-2\s*$",
            "llms-1：RAG 扫盲课程",
            "llms-1",
        ),
        (
            r"^##\s+llms-2\s*$",
            r"^##\s+llms-3\s*$",
            "llms-2：RAG 检索课程",
            "llms-2",
        ),
        (
            r"^##\s+llms-3\s*$",
            r"^##\s+llms-4（RAG入门项目）\s*$",
            "llms-3：RAG From Scratch",
            "llms-3",
        ),
        (
            r"^##\s+llms-4（RAG入门项目）\s*$",
            r"^#\s+✅\s*Agent\s*$",
            "llms-4：RAG 入门项目",
            "starter-project",
        ),
    )

    for start_pattern, end_pattern, title, slug in pages:
        write_page(
            WEB / "rag" / slug / "index.md",
            extract_readme_section(start_pattern, end_pattern, title),
        )


def build_agent() -> None:
    introduction = extract_readme_section(
        r"^#\s+✅\s*Agent\s*$",
        r"^##\s+1\.AI_Agent\s*$",
        "Agent 学习路线",
    )
    content = f"""{introduction}
!!! tip "学习建议"

    1.AI_Agent 和 2.QW_Agent 用于快速建立对 Agent 和 AI 应用开发的整体认知，有个印象即可，不需要逐行过代码或纠结具体实现。学习重点放在后面的系列课程和 Agent 入门项目。

## 内容目录

- [AI Agent 入门 Demo](ai-agent/index.md)
- [千问 Agent Demo](qw-agent/index.md)
- [Google × Kaggle Agent 课程](google-kaggle/index.md)
- [Agent 入门项目：Easy MCP](starter-project/index.md)

## 配套代码

所有 Python 代码、Notebook、白皮书和课程材料继续保留在 GitHub 仓库中。

- [查看 Agent 完整目录]({GITHUB_REPO}/tree/main/2.Agent)
"""

    write_page(WEB / "agent" / "index.md", content)

    ai_agent_source = ROOT / "2.Agent" / "1.AI_Agent"
    ai_agent_destination = WEB / "agent" / "ai-agent"
    ai_agent_summary = extract_readme_section(
        r"^##\s+1\.AI_Agent\s*$",
        r"^##\s+2\.QW_Agent\s*$",
        "AI Agent 入门 Demo",
    )
    ai_agent_details = (ai_agent_source / "README.md").read_text(
        encoding="utf-8"
    )
    write_page(
        ai_agent_destination / "index.md",
        f"""{ai_agent_summary}
---

## 项目详细说明

{demote_headings(ai_agent_details)}
""",
    )
    copy_images(ai_agent_source, ai_agent_destination)

    qw_agent_source = ROOT / "2.Agent" / "2.QW_Agent"
    qw_agent_destination = WEB / "agent" / "qw-agent"
    qw_agent_summary = extract_readme_section(
        r"^##\s+2\.QW_Agent\s*$",
        r"^##\s+3\.Google_and_Kaggle\s*$",
        "千问 Agent Demo",
    )
    qw_agent_details = (qw_agent_source / "README.md").read_text(
        encoding="utf-8"
    )
    write_page(
        qw_agent_destination / "index.md",
        f"""{qw_agent_summary}
---

## 项目详细说明

{demote_headings(qw_agent_details)}
""",
    )
    copy_images(qw_agent_source, qw_agent_destination)

    write_page(
        WEB / "agent" / "google-kaggle" / "index.md",
        extract_readme_section(
            r"^##\s+3\.Google_and_Kaggle\s*$",
            r"^##\s+4\.Agent入门项目\s*$",
            "Google × Kaggle Agent 课程",
        ),
    )

    write_page(
        WEB / "agent" / "starter-project" / "index.md",
        extract_readme_section(
            r"^##\s+4\.Agent入门项目\s*$",
            r"^#\s+✅\s*Interview\s*$",
            "Agent 入门项目：Easy MCP",
        ),
    )


def build_interview() -> None:
    stage_markdown(
        ROOT / "3.Interview" / "README.md",
        WEB / "interview" / "index.md",
        "大模型应用开发面试笔记",
    )


def build_paper_read() -> None:
    paper_root = ROOT / "4.Paper-read" / "paper-read-brief"
    destination = WEB / "paper-read"

    content = """# 论文阅读

这里收录论文速读 Skill 及其生成示例。

## Skill

- [Paper Read Brief 使用说明](skill.md)

## 示例

- [ReAct 速读精要](examples/react.md)
- [Mem0 速读精要](examples/mem0.md)
- [Graph of Thoughts 速读精要](examples/graph-of-thoughts.md)
- [Tree of Thoughts 速读精要](examples/tree-of-thoughts.md)
"""

    write_page(destination / "index.md", content)

    stage_markdown(
        paper_root / "SKILL.md",
        destination / "skill.md",
        "Paper Read Brief",
    )

    examples = (
        ("ReAct速读精要.md", "react.md", "ReAct 速读精要"),
        ("Mem0速读精要.md", "mem0.md", "Mem0 速读精要"),
        (
            "Graph of Thoughts 速读精要.md",
            "graph-of-thoughts.md",
            "Graph of Thoughts 速读精要",
        ),
        (
            "Tree of Thoughts 速读精要.md",
            "tree-of-thoughts.md",
            "Tree of Thoughts 速读精要",
        ),
    )

    for source_name, destination_name, title in examples:
        stage_markdown(
            paper_root / "examples" / source_name,
            destination / "examples" / destination_name,
            title,
        )


def build_site_assets() -> None:
    mathjax_config = r"""window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"]],
    processEscapes: true,
    processEnvironments: true
  },
  options: {
    ignoreHtmlClass: ".*|",
    processHtmlClass: "arithmatex"
  }
};

document$.subscribe(() => {
  MathJax.typesetPromise();
});
"""

    write_page(WEB / "javascripts" / "mathjax.js", mathjax_config)


def main() -> None:
    if WEB.exists():
        shutil.rmtree(WEB)

    WEB.mkdir(parents=True)

    build_home()
    build_roadmap()
    build_rag()
    build_agent()
    build_interview()
    build_paper_read()
    build_site_assets()

    print(f"Website sources generated at: {WEB}")


if __name__ == "__main__":
    main()
