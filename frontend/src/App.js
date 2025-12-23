import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [telegrams, setTelegrams] = useState([]);
  const [selectedTelegram, setSelectedTelegram] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 初回ロード時に一覧を取得
  useEffect(() => {
    fetchTelegrams();
  }, []);

  // 電文一覧取得
  const fetchTelegrams = async () => {
    try {
      const res = await axios.get('/api/telegrams');
      setTelegrams(res.data);
    } catch (err) {
      console.error("Fetch error:", err);
      setError("データの取得に失敗しました。");
    }
  };

  // ファイル選択ハンドラ
  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  // アップロード実行ハンドラ
  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);
    setError(null);

    try {
      await axios.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      await fetchTelegrams();
      setFile(null);
      alert("アップロードと解析が完了しました。");
    } catch (err) {
      console.error("Upload error:", err);
      setError("アップロードまたは解析に失敗しました。");
    } finally {
      setLoading(false);
    }
  };

  // 詳細データの取得
  const handleSelectTelegram = async (id) => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.get(`/api/telegrams/${id}`);
      setSelectedTelegram(res.data);
    } catch (err) {
      console.error("Detail fetch error:", err);
      setError("詳細データの取得に失敗しました。");
    } finally {
      setLoading(false);
    }
  };

  // 日付フォーマット用ヘルパー
  const formatDate = (dateStr) => {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleString('ja-JP');
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>注射オーダ電文照会システム</h1>
      </header>

      <main className="App-container">
        {/* エラー表示 */}
        {error && <div className="error-message">{error}</div>}

        {/* 1. ファイルアップロードセクション */}
        <section className="upload-section">
          <h2>新規電文取込</h2>
          <form onSubmit={handleUpload} className="upload-form">
            <input 
              type="file" 
              onChange={handleFileChange} 
              disabled={loading}
              accept=".txt,.dat,.bin" 
            />
            <button type="submit" disabled={!file || loading}>
              {loading ? '処理中...' : '解析・保存'}
            </button>
          </form>
        </section>

        <div className="content-area">
          {/* 2. 左側: 電文リスト */}
          <section className="list-section">
            <h2>受信履歴</h2>
            {telegrams.length === 0 ? (
              <p>データがありません</p>
            ) : (
              <ul className="telegram-list">
                {telegrams.map((t) => (
                  <li 
                    key={t.id} 
                    onClick={() => handleSelectTelegram(t.id)}
                    className={selectedTelegram && selectedTelegram.id === t.id ? 'active' : ''}
                  >
                    <div className="list-item-header">
                      <span className="patient-name">{t.patient_name || '名称不明'}</span>
                      <span className="patient-id">ID: {t.patient_id}</span>
                    </div>
                    <div className="list-item-sub">
                      オーダ日: {t.order_date || '-'}<br/>
                      取込: {formatDate(t.created_at)}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {/* 3. 右側: 詳細表示 */}
          <section className="detail-section">
            <h2>電文詳細</h2>
            {!selectedTelegram ? (
              <div className="placeholder">左のリストから選択してください</div>
            ) : (
              <div className="detail-content">
                
                {/* 処方項目一覧 */}
                <div className="info-group">
                  <h3>処方項目一覧</h3>
                  <table className="item-table">
                    <thead>
                      <tr>
                        <th>項目名</th>
                        <th>数量</th>
                        <th>単位</th>
                        <th>コード</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedTelegram.raw_data?.content?.item_group?.item_info
                        ?.filter(item => item.attribute === 'ID1').map((item, index) => (
                          <tr key={index}>
                            <td>{item.name}</td>
                            <td>{item.quantity}</td>
                            <td>{item.unit_name}</td>
                            <td>{item.code}</td>
                          </tr>
                        )) || (
                          <tr><td colSpan="4">項目なし</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>

                {/* 患者情報 */}
                <div className="info-group">
                  <h3>患者情報</h3>
                  <div className="info-grid">
                    <div className="info-item">
                      <label>患者ID</label>
                      <span>{selectedTelegram.patient_id}</span>
                    </div>
                    <div className="info-item">
                      <label>患者氏名</label>
                      <span>{selectedTelegram.patient_name}</span>
                    </div>
                    <div className="info-item">
                      <label>生年月日</label>
                      <span>{selectedTelegram.raw_data?.content?.patient_info?.birthdate || '-'}</span>
                    </div>
                    <div className="info-item">
                      <label>住所</label>
                      <span>{selectedTelegram.raw_data?.content?.patient_info?.address || '-'}</span>
                    </div>
                  </div>
                </div>

                {/* オーダ情報 */}
                <div className="info-group">
                  <h3>オーダ情報</h3>
                  <div className="info-grid">
                    <div className="info-item">
                      <label>オーダ番号</label>
                      <span>{selectedTelegram.raw_data?.content?.order_info?.number || '-'}</span>
                    </div>
                    <div className="info-item">
                      <label>版数</label>
                      <span>{selectedTelegram.raw_data?.content?.order_info?.version || '-'}</span>
                    </div>
                    <div className="info-item">
                      <label>依頼医ID</label>
                      <span>{selectedTelegram.raw_data?.content?.order_info?.doctor_info?.d_id || '-'}</span>
                    </div>
                    <div className="info-item">
                      <label>依頼医氏名</label>
                      <span>{selectedTelegram.raw_data?.content?.order_info?.doctor_info?.kanji_name || '-'}</span>
                    </div>
                    <div className="info-item">
                      <label>診療科</label>
                      <span>{selectedTelegram.raw_data?.content?.order_info?.hakkou_dept_code || '-'}</span>
                    </div>
                  </div>
                </div>

                <div className="info-group">
                  <h3>取込情報</h3>
                  <div className="info-grid">
                    <div className="info-item">
                      <label>取込日時</label>
                      <span>{formatDate(selectedTelegram.created_at)}</span>
                    </div>
                    <div className="info-item">
                      <label>最終更新日時</label>
                      <span>{formatDate(selectedTelegram.updated_at)}</span>
                    </div>
                    <div className="info-item">
                      <label>JSON</label>
                      {/* JSON表示のみ、詳細を隠してボタンで展開しても良いかも */}
                      <pre>{JSON.stringify(selectedTelegram.raw_data, null, 2)}</pre>
                    </div> 
                  </div>
                </div>
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}

export default App;