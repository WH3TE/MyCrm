from numpy import char
import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="客户管理前端", layout="wide")

def test():
    st.write("测试")


if "api_base" not in st.session_state:
    st.session_state.api_base = "http://127.0.0.1:8000"

st.sidebar.title("设置")
st.session_state.api_base = st.sidebar.text_input("API 地址", st.session_state.api_base)

def fetch_customers():
    try:
        r = requests.get(f"{st.session_state.api_base}/customers", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"获取客户失败: {e}")
        return []

def create_customer(payload):
    try:
        r = requests.post(f"{st.session_state.api_base}/customers", json=payload, timeout=10)
        r.raise_for_status()
        return r.json(), None
    except requests.HTTPError as e:
        return None, f"创建失败: {e.response.text}"
    except Exception as e:
        return None, f"创建失败: {e}"

def update_customer(customer_id, payload):
    try:
        r = requests.put(f"{st.session_state.api_base}/customers/{customer_id}", json=payload, timeout=10)
        r.raise_for_status()
        return r.json(), None
    except requests.HTTPError as e:
        return None, f"更新失败: {e.response.text}"
    except Exception as e:
        return None, f"更新失败: {e}"

st.title("客户管理系统（Streamlit 前端）")
tab_list, tab_add, tab_edit = st.tabs(["查看客户", "新增客户", "修改客户"])

with tab_list:
    col1, col2 = st.columns([1, 6])
    with col1:
        if st.button("刷新列表"):
            st.session_state.pop("customers_cache", None)
    if "customers_cache" not in st.session_state:
        st.session_state.customers_cache = fetch_customers()
    data = st.session_state.customers_cache
    st.caption(f"共 {len(data)} 位客户")
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("暂无客户数据")

with tab_add:
    with st.form("form_add"):
        name = st.text_input("姓名", key="add_name")
        company = st.text_input("公司", key="add_company")
        position = st.text_input("职位", key="add_position")
        last_contact = st.text_input("最后联系记录", key="add_last_contact")
        submitted = st.form_submit_button("提交新增")
        if submitted:
            payload = {
                "name": name.strip(),
                "company": company.strip(),
                "position": position.strip(),
                "last_contact": last_contact.strip(),
            }
            res, err = create_customer(payload)
            if err:
                st.error(err)
            else:
                # 使用 toast 显示临时提示，几秒后自动消失
                st.toast(f"新增成功，ID={res.get('id')}", icon="✅")
                st.session_state["customers_cache"] = fetch_customers()

with tab_edit:
    customers = st.session_state.get("customers_cache") or fetch_customers()
    if not customers:
        st.info("暂无客户可编辑，请先新增。")
    else:
        id_to_label = {c["id"]: f"{c['id']} - {c['name']}" for c in customers}
        selected_id = st.selectbox("选择客户", options=list(id_to_label.keys()), format_func=lambda x: id_to_label[x], key="edit_select")
        current = next((c for c in customers if c["id"] == selected_id), None)
        if current:
            with st.form("form_edit"):
                name_e = st.text_input("姓名", value=current.get("name", ""), key="edit_name")
                company_e = st.text_input("公司", value=current.get("company", ""), key="edit_company")
                position_e = st.text_input("职位", value=current.get("position", ""), key="edit_position")
                last_contact_e = st.text_input("最后联系记录", value=current.get("last_contact", ""), key="edit_last_contact")
                submitted_e = st.form_submit_button("提交修改")
                if submitted_e:
                    payload = {
                        "name": name_e.strip(),
                        "company": company_e.strip(),
                        "position": position_e.strip(),
                        "last_contact": last_contact_e.strip(),
                    }
                    res, err = update_customer(selected_id, payload)
                    if err:
                        st.error(err)
                    else:
                        # 使用 toast 显示临时提示，几秒后自动消失
                        st.toast("修改成功", icon="✅")
                        st.session_state["customers_cache"] = fetch_customers()
