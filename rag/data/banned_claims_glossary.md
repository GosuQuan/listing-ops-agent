# 禁限词与宣称词表（Listing Ops 参考）

> 说明：本文件为演示用词表摘要，**不能**替代法务/平台最新政策。Agent 检索到本片段时应提示「需人工复核」，不得自动判定合规通过。

## 绝对化与疗效类（高风险）
中英文常见触达示例（不完全列表）：
- 治愈 / cure / treat / heal / anti-disease
- 医用 / medical grade（无资质证明时）
- 灭菌 / sterilize / kill 99.99% germs（无检测报告时）
- 无副作用 / no side effects
- 最有效 / #1 / guaranteed results

宠物湿巾、清洁类目尤其要避免把「清洁爪子」写成治疗皮肤病、止痒特效等医疗表述。可改为：gently cleans paws / helps remove dirt and mud（仅描述清洁动作）。

## 空洞促销与主观夸张
- high quality / best / amazing / perfect / miracle / magic
- 史上最强 / 全网第一 / 秒杀一切
此类词对检索贡献低，且占用标题与五点描述空间。Ops 诊断应标记 empty/hype word，草稿替换为材质、规格、场景。

## 环保与认证类（需凭证）
仅在持有有效证书或供应链文件时可写：
- organic / bio（注意欧盟有机标识规则）
- OEKO-TEX / FSC / compostable（需对应标准编号与适用范围）
禁止：eco-friendly 堆砌但无任何依据；禁止伪造认证编号。竹纤维（bamboo fiber）可作为材质描述，但不要延伸成未证实的「医用竹炭疗愈」等宣称。

## 品牌与竞品
- 不在标题或五点中贬低竞品品牌。
- 不使用未授权的第三方品牌名搭便车（除非平台允许的兼容性说明且符合政策）。
- 自有品牌译名以 glossary 为准，EN/DE 保持同一官方写法。

## 德语站额外注意
- 健康相关宣称受当地与平台规则约束，翻译时不要把 “clean” 强化成 “desinfizierend” 除非有依据。
- 避免全大写堆词；复合名词需正确连接，错误拆分会影响专业感与匹配。

## Agent 使用方式
1. 检索本词表 → 得到候选风险词。
2. 与当前标题/五点做字符串或规范化匹配。
3. 命中则写入 diagnosis 列表，严重级别可分 warning / block。
4. block 级建议在 human_approve 默认倾向 reject，并展示命中证据。
5. 导出文件附带 `banned_hits` 审计字段，便于事后抽检。

## 更新节奏
词表应版本化（例如 glossary_vYYYYMMDD）。评测集中保留正负样本：含 cure 的标题应被打标；仅含 alcohol-free 的清洁描述不应误杀。误杀率与漏检率都要进 CI，而不是只看 demo 能否跑通。

## 与 RAG 模块的关系
本仓库 `rag/` 演示如何把词表与指南切块向量化后供问答与草稿前检索。生产环境可换成公司私有词表，并限制只读权限。检索 top-k 后可选重排序，再交给模型总结「本次草稿需要规避的词」。无模型密钥时，流水线仍应能返回命中片段，保证 Ops 可人工阅读。

## 示例命中说明（PET-WIPE-001 风格）
输入标题含 “high quality” 与重复 “竹纤维”：诊断应至少包含空洞词与重复词；若同时出现 “cure itchy skin”，应升级为禁限宣称并阻止自动导出。正确方向：突出 bamboo fiber、alcohol-free、piece count、dogs & cats、travel pack，并把医疗相关表述完全删除。

## 补充：灰度词（需人工判断）
- sensitive skin / für sensible Haut：可接受时需避免延伸到治疗皮炎。
- natural / natürlich：无标准定义时尽量改用具体材质。
- clinical formula：无临床资料时视为高风险。
灰度词命中默认 warning，不自动 block，但必须在审批 UI 高亮。
词表维护者每月回顾误杀与漏检各 10 例，调整级别。

## 补充：灰度词（需人工判断）
- sensitive skin / für sensible Haut：可接受时需避免延伸到治疗皮炎。
- natural / natürlich：无标准定义时尽量改用具体材质。
- clinical formula：无临床资料时视为高风险。
灰度词命中默认 warning，不自动 block，但必须在审批 UI 高亮。
词表维护者每月回顾误杀与漏检各 10 例，调整级别。

## 补充：灰度词（需人工判断）
- sensitive skin / für sensible Haut：可接受时需避免延伸到治疗皮炎。
- natural / natürlich：无标准定义时尽量改用具体材质。
- clinical formula：无临床资料时视为高风险。
灰度词命中默认 warning，不自动 block，但必须在审批 UI 高亮。
词表维护者每月回顾误杀与漏检各 10 例，调整级别。

## 补充：灰度词（需人工判断）
- sensitive skin / für sensible Haut：可接受时需避免延伸到治疗皮炎。
- natural / natürlich：无标准定义时尽量改用具体材质。
- clinical formula：无临床资料时视为高风险。
灰度词命中默认 warning，不自动 block，但必须在审批 UI 高亮。
词表维护者每月回顾误杀与漏检各 10 例，调整级别。

## 补充：灰度词（需人工判断）
- sensitive skin / für sensible Haut：可接受时需避免延伸到治疗皮炎。
- natural / natürlich：无标准定义时尽量改用具体材质。
- clinical formula：无临床资料时视为高风险。
灰度词命中默认 warning，不自动 block，但必须在审批 UI 高亮。
词表维护者每月回顾误杀与漏检各 10 例，调整级别。

## 补充：灰度词（需人工判断）
- sensitive skin / für sensible Haut：可接受时需避免延伸到治疗皮炎。
- natural / natürlich：无标准定义时尽量改用具体材质。
- clinical formula：无临床资料时视为高风险。
灰度词命中默认 warning，不自动 block，但必须在审批 UI 高亮。
词表维护者每月回顾误杀与漏检各 10 例，调整级别。

## 补充：灰度词（需人工判断）
- sensitive skin / für sensible Haut：可接受时需避免延伸到治疗皮炎。
- natural / natürlich：无标准定义时尽量改用具体材质。
- clinical formula：无临床资料时视为高风险。
灰度词命中默认 warning，不自动 block，但必须在审批 UI 高亮。
词表维护者每月回顾误杀与漏检各 10 例，调整级别。

## 补充：灰度词（需人工判断）
- sensitive skin / für sensible Haut：可接受时需避免延伸到治疗皮炎。
- natural / natürlich：无标准定义时尽量改用具体材质。
- clinical formula：无临床资料时视为高风险。
灰度词命中默认 warning，不自动 block，但必须在审批 UI 高亮。
词表维护者每月回顾误杀与漏检各 10 例，调整级别。
