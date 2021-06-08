import React, {Component} from 'react';
import {Card, Row, Col, Tag} from 'antd';


const colors = [
  "magenta","red","volcano","orange","gold","lime","green","cyan","blue","geekblue","purple"
]

class NodeInfo extends Component {

  render () {
    const {nodeinfo, nodeinfo_loading, selected_people} = this.props;
    if(!nodeinfo.basic_info && !nodeinfo_loading){
      return <div></div>
    }
    if(nodeinfo_loading){
      return <div>
        <Card loading={true} title={selected_people + " loading..."}>
        </Card>
      </div>
    }

    const {basic_info, profile_url, tags} = nodeinfo;
    const { Notes, ...desc} = basic_info;
    const note = Notes;
    const name = desc['ChName'];
    console.log(note, desc, 28);
    const info = (
      <Row>
        <Col span={11} offset={1} style={{marginTop: 10}}>
          <div>
            {profile_url && <img
              alt="example"
              width="100%"
              src={profile_url}
            />}
          </div>
        </Col>
        <Col span={1} />
        <Col span={11} style={{marginTop: 10}}>
          {Object.entries(desc).map((d, index) => {
            return <div key={d[0]}>{d[0] + ':' + d[1]}</div>;
          })}
        </Col>
        <Col span={23} offset={1}>
          <div style={{marginTop: 20}}>
            {tags.map((item, index)=>{
              const color_index = index % colors.length;
              return <Tag color={colors[color_index]}>{item}</Tag>
              })
            }
          </div>
        </Col>
      </Row>
    );

    return (
      <div>
        {desc &&  <Card title={name} hoverable cover={info}>
                  {note}          
                </Card>
        }
      </div>
    );
  }
}

export default NodeInfo;
