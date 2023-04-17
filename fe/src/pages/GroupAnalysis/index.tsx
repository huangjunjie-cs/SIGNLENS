import React, { useState } from 'react';

import { FormattedMessage } from 'umi';
import { Checkbox, Slider, InputNumber, Row, Col, Form, Input, Button, Select } from 'antd';
import { Line } from '@ant-design/charts';

import style from '@/pages/pages.less';

const { Option } = Select;

const layout = {
  labelCol: { span: 8 },
  wrapperCol: { span: 16 },
};
const tailLayout = {
  wrapperCol: { offset: 8, span: 16 },
};


const LineSplit = (totalWidth=100, cutNum=1)=>{
  return Array.from({length: cutNum}).map((v, index)=>{
    const len = totalWidth / cutNum
    return <div style={{ width: '20%', height: 6, backgroundColor: 'green', marginRight: 2}}/>
  })
}
const data = [
  { year: 965.0, value: 0.0 },
{ year: 975.0, value: 0.028169014084507043 },
{ year: 985.0, value: 0.04081632653061224 },
{ year: 995.0, value: 0.05660377358490566 },
{ year: 1005.0, value: 0.02877697841726619 },
{ year: 1015.0, value: 0.02112676056338028 },
{ year: 1025.0, value: 0.07894736842105263 },
{ year: 1035.0, value: 0.0220125786163522 },
{ year: 1045.0, value: 0.014164305949008499 },
{ year: 1055.0, value: 0.0077279752704791345 },
{ year: 1065.0, value: 0.009887005649717515 },
{ year: 1075.0, value: 0.039663461538461536 },
{ year: 1085.0, value: 0.03696098562628337 },
{ year: 1095.0, value: 0.052002390914524806 },
{ year: 1105.0, value: 0.12655601659751037 },
{ year: 1115.0, value: 0.06627906976744186 },
{ year: 1125.0, value: 0.22289156626506024 },
{ year: 1135.0, value: 0.05122950819672131 },
{ year: 1145.0, value: 0.08129032258064516 },
{ year: 1155.0, value: 0.2092274678111588 },
{ year: 1165.0, value: 0.0524390243902439 },
{ year: 1175.0, value: 0.019979508196721313 },
{ year: 1185.0, value: 0.010010537407797681 },
{ year: 1195.0, value: 0.017026850032743943 },
{ year: 1205.0, value: 0.0824 },
{ year: 1215.0, value: 0.024173027989821884 },
{ year: 1225.0, value: 0.02109704641350211 },
{ year: 1235.0, value: 0.03177570093457944 },
{ year: 1245.0, value: 0.017584994138335287 },
{ year: 1255.0, value: 0.06501547987616099 },
{ year: 1265.0, value: 0.10822510822510822 },
{ year: 1275.0, value: 0.19469026548672566 },
{ year: 1285.0, value: 0.015503875968992248 },
];

const config = {
  data,
  height: 400,
  xField: 'year',
  yField: 'value',
  point: {
    size: 5,
    shape: 'diamond',
  },
};

const options = [
  { label: 'Negative Ratio', value: 'negative_ratio' },
  { label: 'Unbalanced Triangle Ratio', value: 'unbalanced_triangle_ratio' },
  { label: 'Frustration Index', value: 'frustration_index' },
  { label: 'Spectral Analysis', value: 'spectral_analysis' },
]

const minT = 117;
const maxT = 1950;

const marks = {
  [minT]: `${minT.toLocaleString()}`,
  [maxT]: `${maxT.toLocaleString()}`
};

console.log(marks, 64);
const GroupAnalysisPage = () => {
  const [beginT, setbeginT] = useState(960);
  const [endT, setendT] = useState(1300);
  const [timeGap, settimeGap] = useState(10);
  const [metrics, setmetrics] = useState(['negative_ratio'])
  return (
    <div className={style.pageContainer}>
      <h2>
        <FormattedMessage id="menu.analysis.group" />
      </h2>
      <br />

      <Row>
        <Col span={16}>
        <Line {...config} />
        </Col>
        <Col span={8}>
        <Form {...layout}  name="control-hooks" >
          <Form.Item name="note" label="Time Gap" rules={[{ required: true }]}>
            <InputNumber min={1} max={100} step={1} defaultValue={timeGap}  value={timeGap} onChange={settimeGap}/>
          </Form.Item>
          <Form.Item name='Time Span' label="Time Span" rules={[{ required: true }]}>
            <Slider 
              marks={marks} 
              range={{ draggableTrack: true }} 
              defaultValue={[beginT, endT]} 
              min={minT} 
              max={maxT}
              value={[beginT, endT]}
              onChange={item=>{setbeginT(item[0]); setendT(item[1])}}
            />
          </Form.Item>
          <Form.Item name='Time Span' label="Begin/End">
            <InputNumber min={beginT} max={endT} step={1} value={beginT} onChange={setbeginT}/>
            <span style={{padding: 10}}>~</span>
            <InputNumber min={beginT} max={endT} step={1} value={endT} onChange={setendT}/>
          </Form.Item>
          <Form.Item name="metric" label="Unbalance Metrics" rules={[{ required: true }]}>
            <Checkbox.Group value={metrics} defaultValue={metrics} onChange={setmetrics} >
            {options.map(item=>{
              
              return (<div><Checkbox value={item['value']}>
                          {item['label']}
                          </Checkbox>
                     </div>)
            })}
            </Checkbox.Group>
          </Form.Item>
          <Form.Item {...tailLayout}>
            <Button type="primary" htmlType="submit">
              Submit
            </Button>
          </Form.Item>
        </Form>

        </Col>
      </Row>
    </div>
  );
};

export default GroupAnalysisPage;
