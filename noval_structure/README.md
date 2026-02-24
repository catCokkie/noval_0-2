# final - ��Ƕ�С˵ AI Э���ܹ�����ذ棩

��Ŀ¼�� `noval_structure` ��ִ�н��Ŀ¼��Ŀ�����ṩһ�׿���ֱ������ AI Э����ƪС˵�������������ּܡ�

## ��������

- `noval_structure` ��Ψһ�ɱ༭���⣨Source of Truth����
- `noval_generate_plan/plan` ������Ϊ��ʷ�鵵���գ�����Ϊ�ճ��༭Ŀ¼��
- �������޸� Canon���滮����ʾ�ʡ���֤����ʱ��ֻ�� `noval_structure` ���̡�

## ���Ŀ��

- �� `opus` ��Ϊ�ںϻ��ߣ����� `gpt/templates` �Ľӿڻ�ģ�塣
- ͨ���̶� Schema ��֤�ɻ��ݡ���У�顢���Զ�����
- ��������Ŀ¼�����ɶ��ԣ�ͬʱ����Ӣ�ļ�����֤�ű������ԡ�

## �������

- �����淶��`agent.md`
- �ܷ������`01_��Ŀ��ʻ��/��Ʒ�ܷ�.md`��`02_��ʷ�ʲ�_Canon/����/Ӳ����_R1-R3.md`
- ���� Schema��`02_��ʷ�ʲ�_Canon/����/���￨_ģ��.yml`
- �����˱���`02_��ʷ�ʲ�_Canon/�����˱�.yml`
- ·����ɱ���`08_�Զ���/ģ��·����ɱ�.yml`

## �Ľ׶�����

1. Canon��������Ʒ�ܷ�������������ʡ�
2. Planning����������¸ٶ��塰���¸ı���ʲô����
3. Draft������ԭʼ�ݸ� -> �޶��ݸ塣
4. Validation���½����ա����Ȼع顢�����ܸ١�

## 10 ����������С�ջ�

1. ����� Canon �ļ��ף��ܷ���Ӳ����3 �����10 �����ʡ�
2. �� `07_��ʾ�ʺ�Լ/20_�¸�����.md` ���� c001-c010 �¸١�
3. �� `30_�����Ǽ�.md` �� `40_������д.md` ���ɲݸ塣
4. �� `60_�����Լ��.md` �� `06_��֤��ع�/�½������嵥.md` �����ա�
5. �� `01_��Ŀ��ʻ��/������ɱ�����.csv` ���³ɱ���״̬��

## ������ԼժҪ

- �½� Front Matter��
  - `chapter_id`, `volume`, `season`, `status`, `pov`, `characters`, `locations`, `new_terms`, `foreshadow_add`, `foreshadow_payoff`, `hook_type`, `model_used`, `token_in`, `token_out`, `cost_usd`
  - �ϸ�У�飺`08_�Զ���/schemas/chapter_front_matter.schema.json`
- ���￨��
  - `id`, `name`, `role`, `voice`, `competence`, `motivation`, `secrets`, `upgrade`, `observability`, `relations`, `last_updated_chapter`
- �����˱���
  - `id`, `seed_chapter`, `expected_payoff_range`, `payoff_chapter`, `status`, `type`, `payload`
- ·����ɱ���
  - `version`, `currency`, `default_budget_limit_usd_per_chapter`, `routing`, `tracking_fields`, `alerts`

## ˵��

- `08_�Զ���/scripts/` Ϊռλ�ű���������ҵ��ʵ�֡�
- ÿ����ṩ��001��ʾ���ļ�������һ�������ɴ��������ļ���

## ��ʷʾ���ı�����

- `04_�ݸ��` �� `05_�����` ��ǰ����Ϊ��ʷʾ���ı���
- ��������δͬ����������߽����� Canon��������Ϊ��ǰ��ֵ��Դ��
- ��ǰ��ֵ�� `01_��Ŀ��ʻ��`��`02_��ʷ�ʲ�_Canon`��`03_�滮��` Ϊ׼��
