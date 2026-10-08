# Search publication (4.10.0, 2026-10-08)

New video articles require an actual 11-character video ID, positive duration and verified upload date. Missing prefilled upload dates must fail, never fall back to the current date. The blog's 2.8.0 release gate inventories all rendered routes and fields; hidden/password/private/noindex content is excluded from discovery feeds and watch pages. FAQ schema is explicit opt-in for visible factual FAQ only.

Use the canonical `npm run publish` contract, including post-deploy live checks and downstream knowledge/resource synchronization. IndexNow runs only after deployment and matching public content; acceptance does not establish indexing. Refer to the blog's `docs/site-search-governance.md` for the field matrix, source/build snapshot gate and bounded retry procedure. Do not generate unrelated old-post rewrites or new media as part of an SEO-only maintenance run.

Prefer actual blog body sentences for descriptions. Do not invent steps, FAQ or deployment coverage from the title. Short factual descriptions are acceptable and receive an advisory, not padding. The 160-character limit is a project convention, not a fixed Google snippet rule.

Before publishing, provide two relevant root-relative article links and verify their destinations. Run strict single-post SEO and full build audits. Standalone auto-deploy commits only the generated post and its local cover, refuses existing staging or unrelated changes, and uses the blog's `npm run publish` (including downstream synchronization). `--no-deploy` always suppresses auto-deploy. Failures return nonzero.

Existing filenames are rejected without writing timestamp duplicates. Resume upstream with `--blog-post`; preserve date, category and permalink. Hidden content stays noindex until explicitly released, then must pass checks again.

YouTube playlists are author-managed. This Skill records the exact `video_id` and uses the blog's shared publisher, but must not add/remove playlist items or infer a permanent topic from title keywords. After the author maintains playlists and requests notification, the notification pipeline performs a new strict playlist export, topic build, deployment and public-fingerprint verification. Failures block notification and are retried without regenerating the article or uploading another video.

## Earlier front-matter history

- 2026-07-28: v4.8.2 对齐博客 v2.3.2；观看页只允许一个完整 JSON-LD VideoObject，禁止重复且不完整的 Microdata 视频实体
- 2026-07-28: v4.8.1 对齐博客 v2.3.1；独立观看页播放器必须位于 H1 和说明文字之前，确保 Google 首屏可见与主体突出
- 2026-07-28: v4.8.0 对齐博客 v2.3.0 页面职责分离；源 iframe 仅供 Hexo 生成观看页，渲染文章只输出封面入口，播放器与 VideoObject 仅允许出现在 /videos/<video_id>/
- 2026-07-27: v4.7.1 明确生成文章永久链接会自动进入独立观看页的对应博客文章区域，发布门禁验证目标 HTML 真实存在
- 2026-07-27: v4.7.0 对齐博客 v2.2.0 独立观看页契约；生成的 video_id 等元数据会在 Hexo 构建时自动产生 /videos/<video_id>/、视频索引和 video-sitemap.xml
- 2026-07-27: v4.6.3 强制 video_upload_date 为带时区的有效 ISO 8601，优先使用 YouTube timestamp，并拒绝无时区或非法预填值
- 2026-07-26: v4.6.2 明确保留 body_md fenced code block，并增加回归测试，确保 Hexo 主题可为生成代码块附加复制按钮
- 2026-07-26: v4.6.1 修复 generate_seo_description 把 hashtag 列表当作 SEO description 的 bug——在提取候选句前先移除 # 开头的 hashtag token
- 2026-07-23: v4.6.0 清除新旧 YouTube 描述和 body_md 中无效的"复制到浏览器"提示，避免重新写回博客正文
- 2026-07-22: v4.5.0 输出 VideoObject 所需 front matter、自然摘要 excerpt、最多 5 个标签，移除伪相关推荐首页链接，并与博客 SEO 门禁对齐
- 2026-07-18: v4.4.0 body_md 路径在保留原始 Markdown 正文后追加完整 YouTube description；固定板块支持“纯净住宅IP白嫖流量”标题别名；禁用破坏正文语义和 SEO 关键词的词级 humanize 替换
- 2026-05-23: v4.3.2 YAML 安全转义——新增 yaml_safe_string() 对 front matter 的 title/description 字段做双引号包裹+内部转义，防止 **bold** 和 [links] 被 YAML 误解析为 alias 或 sequence；iframe title 属性同步做 HTML 引号转义
- 2026-05-23: v4.3.1 严格执行规则——新增「🔴 严格执行规则（最高优先级）」章节于 SKILL.md 顶部，强制 AI 严格按文档执行每一步、实跑 youtube_to_post.py 脚本、不跳过 SEO 优化步骤、部署后必须验证
