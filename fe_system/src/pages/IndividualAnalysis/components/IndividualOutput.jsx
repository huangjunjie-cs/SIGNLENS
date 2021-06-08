import React from 'react';
import { Tabs, Col, Row } from 'antd';

import TopPeople from './outputs/part1/topPeople';
import DirectGraph from './outputs/part2/directGraph';
import ForchGraph from './outputs/part3/forchGraph';
import NodeInfo from './outputs/part3/nodeInfo';

import { FormatMess} from 'umi'

// import { getPeopleProfile } from '../api';

const TabPane = Tabs.TabPane;

let nodes = {
  3762: {
    position: [-0.49999989, -0.86602541],
    name: 'Su Xun',
    centrality: {
      c1: 0.002,
      c2: 0.001,
      PersonID: '3762',
      c4: 0.024,
      EngName: 'Su Xun',
      ChName: '\u8607\u6d35',
      c3: 0.292,
    },
  },
  1762: {
    position: [0.49999998, 0.86602546],
    name: 'Wang Anshi',
    centrality: {
      c1: 0.025,
      c2: 0.054,
      PersonID: '1762',
      c4: 0.138,
      EngName: 'Wang Anshi',
      ChName: '\u738b\u5b89\u77f3',
      c3: 0.361,
    },
  },
  7364: {
    position: [-9.9999997e-1, -6.29182054e-8],
    name: 'Zeng Gong',
    centrality: {
      c1: 0.011,
      c2: 0.019,
      PersonID: '7364',
      c4: 0.062,
      EngName: 'Zeng Gong',
      ChName: '\u66fe\u978f',
      c3: 0.335,
    },
  },
  1493: {
    position: [1.0, 2.45045699e-8],
    name: 'Su Zhe',
    centrality: {
      c1: 0.007,
      c2: 0.009,
      PersonID: '1493',
      c4: 0.07,
      EngName: 'Su Zhe',
      ChName: '\u8607\u8f4d',
      c3: 0.338,
    },
  },
  3767: {
    position: [-0.50000004, 0.8660254],
    name: 'Su Shi',
    centrality: {
      c1: 0.029,
      c2: 0.083,
      PersonID: '3767',
      c4: 0.179,
      EngName: 'Su Shi',
      ChName: '\u8607\u8efe',
      c3: 0.38,
    },
  },
  1384: {
    position: [0.49999992, -0.86602541],
    name: 'Ouyang Xiu',
    centrality: {
      c1: 0.022,
      c2: 0.046,
      PersonID: '1384',
      c4: 0.135,
      EngName: 'Ouyang Xiu',
      ChName: '\u6b50\u967d\u4fee',
      c3: 0.362,
    },
  },
};

let links1 = [
  {
    source: '1762',
    target: '7364',
    id: '8814',
    weight: 1.0,
  },
  {
    source: '1762',
    target: '1384',
    id: '8613',
    weight: 5.0,
  },
  {
    source: '1762',
    target: '3767',
    id: '8796',
    weight: 1.0,
  },
  {
    source: '1493',
    target: '3767',
    id: '22706',
    weight: 6.0,
  },
  {
    source: '1493',
    target: '3762',
    id: '21310',
    weight: 3.0,
  },
  {
    source: '1493',
    target: '1384',
    id: '22712',
    weight: 4.0,
  },
  {
    source: '3762',
    target: '1384',
    id: '21313',
    weight: 5.0,
  },
  {
    source: '3762',
    target: '7364',
    id: '21319',
    weight: 1.0,
  },
  {
    source: '3762',
    target: '3767',
    id: '21311',
    weight: 4.0,
  },
  {
    source: '1384',
    target: '7364',
    id: '23479',
    weight: 7.0,
  },
  {
    source: '1384',
    target: '3767',
    id: '23474',
    weight: 10.0,
  },
];

let links2 = [
  {
    id: '1249',
    weight: 0.0,
    source: '1493',
    target: '3767',
  },
  {
    id: '1247',
    weight: -1.0,
    source: '1493',
    target: '1762',
  },
  {
    id: '3826',
    weight: 0.0,
    source: '1384',
    target: '3767',
  },
  {
    id: '1618',
    weight: 0.0,
    source: '1384',
    target: '3762',
  },
  {
    id: '2984',
    weight: 0.0,
    source: '1384',
    target: '7364',
  },
  {
    id: '4466',
    weight: -1.0,
    source: '1384',
    target: '1762',
  },
  {
    id: '2981',
    weight: 0.0,
    source: '3767',
    target: '7364',
  },
  {
    id: '3850',
    weight: -1.0,
    source: '3767',
    target: '1762',
  },
  {
    id: '2986',
    weight: 0.0,
    source: '1762',
    target: '7364',
  },
];

let links3 = [
  {
    source: '1493',
    weight: 4.0,
    target: '1384',
    id: '25787',
  },
  {
    source: '1493',
    weight: 6.0,
    target: '3767',
    id: '25812',
  },
  {
    source: '1493',
    weight: -1.0,
    target: '1762',
    id: '10312',
  },
  {
    source: '1493',
    weight: 3.0,
    target: '3762',
    id: '24000',
  },
  {
    source: '1762',
    weight: 1.0,
    target: '7364',
    id: '10285',
  },
  {
    source: '1762',
    weight: 0.0,
    target: '3767',
    id: '10267',
  },
  {
    source: '1762',
    weight: 4.0,
    target: '1384',
    id: '10042',
  },
  {
    source: '3767',
    weight: 10.0,
    target: '1384',
    id: '26871',
  },
  {
    source: '3767',
    weight: 4.0,
    target: '3762',
    id: '24001',
  },
  {
    source: '3767',
    weight: 0.0,
    target: '7364',
    id: '27449',
  },
  {
    source: '7364',
    weight: 1.0,
    target: '3762',
    id: '24008',
  },
  {
    source: '7364',
    weight: 7.0,
    target: '1384',
    id: '26968',
  },
  {
    source: '3762',
    weight: 5.0,
    target: '1384',
    id: '24003',
  },
];

let link_datas = {
  directed: false,
  graph: {
    mode: 'static',
    edge_default: {},
  },
  links: [
    { value: 4.0, source: '1493', target: '1384' },
    { value: 4.0, source: '1384', target: '1493' },
    { value: 6.0, source: '1493', target: '3767' },
    { value: 6.0, source: '3767', target: '1493' },
    { value: -1.0, source: '1493', target: '1762' },
    { value: -1.0, source: '1762', target: '1493' },
    { value: 3.0, source: '1493', target: '3762' },
    { value: 3.0, source: '3762', target: '1493' },
    { value: 1.0, source: '1762', target: '7364' },
    { value: 1.0, source: '7364', target: '1762' },
    { value: 0.0, source: '1762', target: '3767' },
    { value: 0.0, source: '3767', target: '1762' },
    { value: 4.0, source: '1762', target: '1384' },
    { value: 4.0, source: '1384', target: '1762' },
    { value: 10.0, source: '3767', target: '1384' },
    { value: 10.0, source: '1384', target: '3767' },
    { value: 4.0, source: '3767', target: '3762' },
    { value: 4.0, source: '3762', target: '3767' },
    { value: 0.0, source: '3767', target: '7364' },
    { value: 0.0, source: '7364', target: '3767' },
    { value: 1.0, source: '7364', target: '3762' },
    { value: 1.0, source: '3762', target: '7364' },
    { value: 7.0, source: '7364', target: '1384' },
    { value: 7.0, source: '1384', target: '7364' },
    { value: 5.0, source: '3762', target: '1384' },
    { value: 5.0, source: '1384', target: '3762' },
  ],
  nodes: [
    { group: 1, id: '1762', label: '1762', name: 'Wang Anshi' },
    { group: 2, id: '1493', label: '1493', name: 'Su Zhe' },
    { group: 2, id: '3762', label: '3762', name: 'Su Xun' },
    { group: 1, id: '1384', label: '1384', name: 'Ouyang Xiu' },
    { group: 1, id: '7364', label: '7364', name: 'Zeng Gong' },
    { group: 2, id: '3767', label: '3767', name: 'Su Shi' },
  ],
  multigraph: false,
};

let subgraph_info = {
  pos_tie_num: 3, 
  neg_tie_num: 75, 
  node_num: 6
}

class IndividualOutput extends React.Component {
  state = {
    selected_node_id: '',
    selected_people: '',
    nodeinfo_loading: false,
    nodeinfo: {},
  };

  handleSelectedPeople = (node_id, node_name) => {
    this.setState(
      {
        selected_node_id: node_id,
        selected_people: node_name,
        nodeinfo_loading: true,
      },
      () => {
        // getPeopleProfile(node_id).then(res=>{
        //     const data= res.data;
        //     this.setState({
        //         nodeinfo_loading: false,
        //         nodeinfo: data
        //     })
        // }).catch(err=>{
        //     this.setState({
        //         disabled: true
        //     })
        // })
      },
    );
  };

  render() {
    // {nodes,  links1, links2, links3, link_datas, subgraph_info} = this.props.data;
    let name_dict = {};
    let centrality_data = [];
    let node_list = [];
    for (const key in nodes) {
      name_dict[key] = nodes[key].name;
      node_list.push([key, nodes[key].position]);
      centrality_data.push(nodes[key].centrality);
    }
    

    return node_list.length > 0 ? (
      <div>
        <Tabs tabPosition={'top'}>
      
          <TabPane tab="Top and Central People" key="0" >
            <TopPeople 
              centrality_data={centrality_data} 
              subgraph_info={subgraph_info}
            />
          </TabPane>
          <TabPane tab="Direct Relationship" key="1" >
            <DirectGraph
              name_dict={name_dict}
              node_list={node_list}
              links1={links1}
              links2={links2}
              links3={links3}
            />
          </TabPane>
          <TabPane tab="Group Partition" key="2" >
            <Row gutter={10}>
              <Col lg={16} xs={24} id="forced-graph">
                <ForchGraph
                  links={links3}
                  handleSelctedPeople={this.handleSelectedPeople}
                  datas={link_datas}
                />
              </Col>
              <Col lg={8} xs={24}>
                <NodeInfo
                  selected_people={this.state.selected_people}
                  nodeinfo={this.state.nodeinfo}
                  nodeinfo_loading={this.state.nodeinfo_loading}
                />
              </Col>
            </Row>
          </TabPane>
          
        </Tabs>
      </div>
    ) : (
      <div />
    );
  }
}

export default IndividualOutput;
