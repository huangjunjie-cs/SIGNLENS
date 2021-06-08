import React, { useState } from 'react';
import { Upload, message, Row, Col } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import { FormattedMessage, useIntl } from 'umi';
import style from '@/pages/pages.less';

import { Descriptions } from 'antd';

const { Dragger } = Upload;

const props = {
  name: 'file',
  multiple: true,
  action: 'https://www.mocky.io/v2/5cc8019d300000980a055e76',
  onChange(info) {
    const { status } = info.file;
    if (status !== 'uploading') {
      console.log(info.file, info.fileList);
    }
    if (status === 'done') {
      message.success(`${info.file.name} file uploaded successfully.`);
    } else if (status === 'error') {
      message.error(`${info.file.name} file upload failed.`);
    }
  },
};

const initialState = {
  'node_num':  144184,
  'node_num_in_graph': 33429,
  'edge_note_num': 451,
  'positive_num': 144184,
  'negative_num': 4875,
  'negative_ratio': 4875/(144184+4875),
  'time_begin': 117,
  'time_end': 195,
}

const DataInput = () => {
  const intl = useIntl();
  const [networkInfo, setnetworkInfo] = useState(initialState)
  const [datasetName, setdatasetName] = useState('cbdb')
  return (
    <div className={style.pageContainer}>
      <h2>
        {intl.formatMessage({
          id: 'menu.analysis.data_input',
          defaultMessage: 'Data Input'
        }) }
      </h2>
      <Row gutter={8} style={{paddingBottom: 50}}>
        <Col span={8}>
          <h3>EdgeList</h3>
          <Dragger {...props}>
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">Click or drag file to this area to upload</p>
            <p className="ant-upload-hint">
              Support for a single file upload (please upload tsv file). 
            </p>
          </Dragger>
        </Col>
        <Col span={8}>
          <h3>EdgeInfo</h3>
          <Dragger {...props}>
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">Click or drag file to this area to upload</p>
            <p className="ant-upload-hint">
              Support for a single file upload (please upload tsv file). 
            </p>
          </Dragger>
        </Col>
        <Col span={8}>
          <h3>NodeInfo</h3>
          <Dragger {...props}>
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">Click or drag file to this area to upload</p>
            <p className="ant-upload-hint">
              Support for a single file upload (please upload tsv file). 
            </p>
          </Dragger>
        </Col>
      </Row>
      <br></br>
      <h2>
        {intl.formatMessage({
          id: 'analysis.data_input.network_info',
          defaultMessage: 'Signed Network Info'
        }) }
      </h2>
      <Row>
        <Descriptions title={`Data Decription for ${datasetName}`}>
            {Object.entries(networkInfo).map( item =>{
              console.log(`analysis.data_input.${item[0]}`, item[1]);
              return (<Descriptions.Item label={
                intl.formatMessage({
                  id: `analysis.data_input.${item[0]}`,
                  defaultMessage: `${item[0]}`
                }) 
                }>
                {item[1].toLocaleString()}
              </Descriptions.Item>)
            })
            }
        </Descriptions>
      </Row>
    </div>
  );
};
export default DataInput;
