import click

from .deduper import FileDeduper


@click.command()
@click.argument("directories", nargs=-1, required=True)
@click.option(
    "--mode",
    "-m",
    type=click.Choice(["hash", "fuzzy"], case_sensitive=False),
    default="hash",
    help="去重模式：hash（基于内容哈希）或 fuzzy（基于文件名模糊匹配）",
)
@click.option(
    "--hash-algorithm",
    "-a",
    type=click.Choice(["md5", "sha1", "sha256", "sha512"], case_sensitive=False),
    default="sha256",
    help="哈希算法（仅适用于 hash 模式）",
)
@click.option(
    "--fuzzy-threshold",
    "-t",
    type=float,
    default=0.8,
    help="模糊匹配相似度阈值（0.0-1.0，仅适用于 fuzzy 模式）",
)
@click.option(
    "--exclude-dir",
    "-x",
    multiple=True,
    help="要排除的目录名（可多次使用）",
)
@click.option(
    "--include",
    "-i",
    multiple=True,
    help="包含的文件 glob 模式（可多次使用，如 *.txt）",
)
@click.option(
    "--exclude",
    "-e",
    multiple=True,
    help="排除的文件 glob 模式（可多次使用，如 *.log）",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="JSON 报告输出文件路径",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="显示详细信息",
)
def main(
    directories,
    mode,
    hash_algorithm,
    fuzzy_threshold,
    exclude_dir,
    include,
    exclude,
    output,
    verbose,
):
    """
    文件去重 CLI 工具

    DIRECTORIES: 一个或多个要扫描的目录路径

    功能：
    - 基于内容哈希的重复文件比对
    - 基于文件名模糊匹配的重复检测
    - 支持排除目录和 glob 规则过滤
    - 输出 JSON 格式报告
    """
    if not directories:
        click.echo("错误：请指定至少一个目录路径", err=True)
        return

    exclude_dirs = list(exclude_dir) if exclude_dir else None
    include_glob = list(include) if include else None
    exclude_glob = list(exclude) if exclude else None

    deduper = FileDeduper(
        directories=list(directories),
        exclude_dirs=exclude_dirs,
        include_glob=include_glob,
        exclude_glob=exclude_glob,
        mode=mode,
        hash_algorithm=hash_algorithm,
        fuzzy_threshold=fuzzy_threshold,
    )

    if verbose:
        click.echo(f"扫描模式: {mode}")
        click.echo(f"扫描目录: {', '.join(directories)}")
        if exclude_dirs:
            click.echo(f"排除目录: {', '.join(exclude_dirs)}")
        if include_glob:
            click.echo(f"包含模式: {', '.join(include_glob)}")
        if exclude_glob:
            click.echo(f"排除模式: {', '.join(exclude_glob)}")
        click.echo("")

    click.echo("正在扫描文件...")
    duplicates = deduper.find_duplicates()

    total_groups = len(duplicates)
    total_files = sum(len(files) for files in duplicates.values())

    click.echo(f"发现 {total_groups} 组重复文件，共 {total_files} 个文件")
    click.echo("")

    for group_key, files in duplicates.items():
        click.echo(f"组: {group_key}")
        click.echo(f"  文件数: {len(files)}")
        for i, file_info in enumerate(files):
            click.echo(f"  [{i+1}] {file_info['path']}")
            if verbose:
                click.echo(f"       大小: {file_info['size']} 字节")
        click.echo("")

    if output:
        json_report = deduper.generate_json_report(output_path=output)
        click.echo(f"JSON 报告已保存到: {output}")
    else:
        json_report = deduper.generate_json_report()
        if verbose:
            click.echo("JSON 报告:")
            click.echo(json_report)


if __name__ == "__main__":
    main()
