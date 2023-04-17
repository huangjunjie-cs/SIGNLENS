import component from './zh-CN/component';
import globalHeader from './zh-CN/globalHeader';
import menu from './zh-CN/menu';
import pwa from './zh-CN/pwa';
import settingDrawer from './zh-CN/settingDrawer';
import settings from './zh-CN/settings';
import pages from './zh-CN/pages';

export default {
  'navBar.lang': '语言',
  'layout.user.link.help': '帮助',
  'layout.user.link.privacy': '隐私',
  'layout.user.link.terms': '条款',
  'app.preview.down.block': '下载此页面到本地项目',
  'app.welcome.link.fetch-blocks': '获取全部区块',
  'app.welcome.link.block-list': '基于 block 开发，快速构建标准页面',
  ...pages,
  ...globalHeader,
  ...menu,
  ...settingDrawer,
  ...settings,
  ...pwa,
  ...component,
  'analysis.individual.parameter_setting': '参数设置',
  'analysis.individual.top_and_central_people': '节点中心性',
  'analysis.individual.directed_relationship': '节点直接关系',
  'analysis.individual.group_partition': '组划分',
  'analysis.data_input.network_info': '符号网络信息',
  'analysis.data_input.node_num':  '节点数',
  'analysis.data_input.node_num_in_graph': '网络节点数',
  'analysis.data_input.edge_note_num': '边种类',
  'analysis.data_input.positive_num': '正边数量',
  'analysis.data_input.negative_num': '负边数量',
  'analysis.data_input.negative_ratio': '负边比例',
  'analysis.data_input.time_begin': '开始时间',
  'analysis.data_input.time_end': '结束时间',
};
