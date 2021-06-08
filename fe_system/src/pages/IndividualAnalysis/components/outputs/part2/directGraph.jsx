import React, {Component} from 'react';
import {Card, Col, Row} from 'antd';
import {Divider} from 'antd';

import OriginGraph from './components/originGraph';
import LinkInfo from './components/linkInfo';


// import { getXYRelationship } from '../../../api'; 


class DirectGraph extends Component {
  state = {
    x: '1762',
    y: '1384',
    x_name: '王安石',
    y_name: '欧阳修',
    relations: [],
    loading: false
  };


  handleXYChange = ( x,y ) => {
    console.log(x, y, 404);
    this.setState({
        loading: true
      }, ()=>{
        // getXYRelationship(x, y)
        //   .then(res=>{
        //     const data = res.data
        //     this.setState({
        //       x,
        //       y,
        //       x_name: data.x_name,
        //       y_name: data.y_name,
        //       relations: data.relations
        //     })
        //   }).catch(err=>{
        //     console.log(err)
        // });
    });
  }

  render () {
    const {links1, links2, links3, node_list, name_dict} = this.props;
    return (
      <div>
        <Divider orientation="left"><h3>DirectGraph</h3></Divider>
        <Row gutter={16}>
          <Col lg={8} xs={24}>
            <Card title="Positive Tie" style={{textAlign: 'center'}}>
              <OriginGraph
                key={1}
                node_list={node_list}
                name_dict={name_dict}
                links={links1}
                handleXYChange = {this.handleXYChange}
              />
            </Card>
          </Col>
          <Col lg={8} xs={24}>
            <Card title="Negative Tie" style={{textAlign: 'center'}}>
              <OriginGraph
                key={2}
                node_list={node_list}
                name_dict={name_dict}
                links={links2}
                handleXYChange = {this.handleXYChange}
              />
            </Card>
          </Col>
          <Col lg={8} xs={24}>
            <Card title="Signed Graph" style={{textAlign: 'center'}}>
              <OriginGraph
                key={3}
                node_list={node_list}
                name_dict={name_dict}
                links={links3}
                handleXYChange = {this.handleXYChange}
              />
            </Card>
          </Col>
        </Row>
        {this.state.relations.length > 0 &&
          <div>
            <Divider orientation="left"><h3>LinkInfo</h3></Divider>
            <LinkInfo x={this.state.x_name} y={this.state.y_name} relations={this.state.relations} />
          </div>
        }
          
      </div>
    );
  }
}

export default DirectGraph;
