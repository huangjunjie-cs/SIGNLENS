import React from 'react';
import { FormattedMessage } from 'umi';
import { Row, Col, Card, Form, Slider, InputNumber, Select, Radio, Button, Spin } from 'antd';
import { CaretRightOutlined, CaretDownOutlined } from '@ant-design/icons';
import debounce from 'lodash/debounce';

import IndividualOutput from './components/IndividualOutput';

import {getNodeList, getIndividualAnalysis} from '@/services/api';

import style from '@/pages/pages.less';

const RadioGroup = Radio.Group;
const FormItem = Form.Item;

const defaultPeopleNode = [{"label": "Zeng Gong", "value": "7364"}, {"label": "Su Xun", "value": "3762"}, {"label": "Wang Anshi", "value": "1762"}, {"label": "Su Zhe", "value": "1493"}, {"label": "Su Shi", "value": "3767"}, {"label": "Ouyang Xiu", "value": "1384"}]


function DebounceSelect({ fetchOptions, debounceTimeout = 800, ...props }) {
  const [fetching, setFetching] = React.useState(false);
  const [options, setOptions] = React.useState([{"label": "Zeng Gong", "value": "7364"}, {"label": "Su Xun", "value": "3762"}, {"label": "Wang Anshi", "value": "1762"}, {"label": "Su Zhe", "value": "1493"}, {"label": "Su Shi", "value": "3767"}, {"label": "Ouyang Xiu", "value": "1384"}]);
  const fetchRef = React.useRef(0);
  const debounceFetcher = React.useMemo(() => {
    const loadOptions = (value) => {
      fetchRef.current += 1;
      const fetchId = fetchRef.current;
      setOptions([]);
      setFetching(true);
      fetchOptions(value).then((newOptions) => {
        if (fetchId !== fetchRef.current) {
          // for fetch callback order
          return;
        }
        setOptions(newOptions);
        setFetching(false);
      });
    };

    return debounce(loadOptions, debounceTimeout);
  }, [fetchOptions, debounceTimeout]);
  return (
    <Select
      labelInValue
      filterOption={false}
      defaultValue={['1384', '3762', '1493', '3767', '1762', '7364']}
      onSearch={debounceFetcher}
      notFoundContent={fetching ? <Spin size="small" /> : null}
      {...props}
      options={options}
    />
  );
}

async function fetchUserList(username) {
  console.log('fetching user', username);
  return getNodeList(username)
          .then(res=>{
            console.log(res);
            return res.results.map((it)=>({
              label: it.label,
              value: it.value
            }))
          });
}

class IndividualAnalysisPage extends React.Component {
  state = {
    nodes: defaultPeopleNode,
    algorithm: 1,
    depth: 0,
    showParameter: true,
    key: 'tab1',
    showInput: true,
    outputData: {}
  };

  handlePeopleChange = (value: any) => {
    this.setState({
      nodes: value,
    });
  };

  handleAlgorithmChange = (e) => {
    const algorithm = e.target ? e.target.value : e;
    this.setState({
      algorithm,
    });
  };

  handleDepthChange = (e) => {
    const depth = e.target ? e.target.value : e;
    this.setState({
      depth,
    });
  };

  handleSubmit = () => {
    const params = { 
        nodes: this.state.nodes,
        algorithm: this.state.algorithm,
        depth: this.state.depth 
    };
    console.log(params, 109);
    // this.props.handleSubmit(data);
    getIndividualAnalysis(params)
      .then(res=>{
        console.log(res)
      });
  };

  handleReset = () => {
    this.setState({
      nodes: defaultPeopleNode,
      algorithm: 1,
      depth: 0,
    });
  };

  onTabChange = (key, type) => {
    this.setState({
      [type]: key,
    });
  };

  onShowInputChange = () => {
    this.setState({
      showInput: !this.state.showInput,
    });
  };

  componentWillMount() {
   
  }

  render() {
    const radioStyle = {
      display: 'block',
      height: '30px',
      lineHeight: '30px',
    };
    return (
      <div className={style.pageContainer}>
        <h2>{<FormattedMessage id={'menu.analysis.individual'} />}</h2>
        <a href="#href" onClick={this.onShowInputChange}>
          {this.state.showInput ? <CaretDownOutlined /> : <CaretRightOutlined />}
          <span>
            <FormattedMessage id="analysis.individual.parameter_setting" />
          </span>
        </a>
        {this.state.showInput && (
          <Card>
            <Form onSubmit={this.handleSubmit}>
              <FormItem label="Nodes">
                <Row>
                  <Col span={20}>
                    <DebounceSelect
                        mode="multiple"
                        value={this.state.nodes}
                        placeholder="Select nodes"
                        fetchOptions={fetchUserList}
                        onChange={this.handlePeopleChange}
                        style={{
                          width: '100%',
                        }}
                      />
                  </Col>
                </Row>
                
              </FormItem>
              <FormItem label="Depth">
                <Row>
                  <Col span={8}>
                    <Slider
                      min={0}
                      max={3}
                      onChange={this.handleDepthChange}
                      value={this.state.depth}
                    />
                  </Col>
                  <Col span={4}>
                    <InputNumber
                      min={0}
                      max={3}
                      style={{ width: '4em', marginLeft: '20%' }}
                      value={this.state.depth}
                      onChange={this.handleDepthChange}
                    />
                  </Col>
                </Row>
              </FormItem>
              <FormItem label="Algorithm">
                <RadioGroup onChange={this.handleAlgorithmChange} value={this.state.algorithm}>
                  <Radio style={radioStyle} value={1}>
                    Community Detection
                  </Radio>
                  <Radio style={radioStyle} value={2} disabled>
                    Network Embedding
                  </Radio>
                </RadioGroup>
              </FormItem>
              <div>
                <Button type="primary" onClick={this.handleSubmit} style={{ margin: 5 }}>
                  CONFIRM
                </Button>
                <Button onClick={this.handleReset} style={{ margin: 5 }}>
                  RESET
                </Button>
              </div>
            </Form>
          </Card>
        )}
        <IndividualOutput />
      </div>
    );
  }
}

export default IndividualAnalysisPage;
