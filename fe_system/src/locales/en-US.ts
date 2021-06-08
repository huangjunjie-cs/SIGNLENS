import component from './en-US/component';
import globalHeader from './en-US/globalHeader';
import menu from './en-US/menu';
import pwa from './en-US/pwa';
import settingDrawer from './en-US/settingDrawer';
import settings from './en-US/settings';
import pages from './en-US/pages';

export default {
  'navBar.lang': 'Languages',
  'layout.user.link.help': 'Help',
  'layout.user.link.privacy': 'Privacy',
  'layout.user.link.terms': 'Terms',
  'app.preview.down.block': 'Download this page to your local project',
  'app.welcome.link.fetch-blocks': 'Get all block',
  'app.welcome.link.block-list': 'Quickly build standard, pages based on `block` development',
  ...globalHeader,
  ...menu,
  ...settingDrawer,
  ...settings,
  ...pwa,
  ...component,
  ...pages,
  'analysis.individual.parameter_setting': 'Parameter Setting',
  'analysis.individual.top_and_central_people': 'Top and Central People',
  'analysis.individual.directed_relationship': 'Direct Relationship',
  'analysis.individual.group_partition': 'Group Partition',
  'analysis.data_input.network_info': 'Signed Network Info',
  'analysis.data_input.node_num':  '#Node',
  'analysis.data_input.node_num_in_graph': '#Node in Graph',
  'analysis.data_input.edge_note_num': '#Edge Type',
  'analysis.data_input.positive_num': '#Positive Links',
  'analysis.data_input.negative_num': '#Negative Links',
  'analysis.data_input.negative_ratio': '%Negative Ratio',
  'analysis.data_input.time_begin': 'Begin Time',
  'analysis.data_input.time_end': 'End Time',
};
