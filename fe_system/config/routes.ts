export default [
  {
    path: '/user',
    layout: false,
    routes: [
      {
        path: '/user',
        routes: [
          {
            name: 'login',
            path: '/user/login',
            component: './User/login',
          },
        ],
      },
    ],
  },
  {
    path: '/welcome',
    name: 'welcome',
    icon: 'smile',
    component: './Welcome',
  },
  {
    path: '/admin',
    name: 'admin',
    icon: 'crown',
    access: 'canAdmin',
    component: './Admin',
    routes: [
      {
        path: '/admin/sub-page',
        name: 'sub-page',
        icon: 'smile',
        component: './Welcome',
      },
    ],
  },
  {
    name: 'analysis.data_input',
    icon: 'FileAddOutlined',
    path: '/data_input',
    component: './DataInput',
  },
  {
    name: 'analysis.individual',
    icon: 'UserOutlined',
    path: '/individual-analysis',
    component: './IndividualAnalysis',
  },
  {
    name: 'analysis.group',
    icon: 'LineChartOutlined',
    path: '/group-analysis',
    component: './GroupAnalysis',
  },
  {
    name: 'analysis.about',
    icon: 'InfoCircleOutlined',
    path: '/about',
    component: './About',
  },
  {
    path: '/',
    redirect: '/welcome',
  },
  {
    component: './404',
  },
];
