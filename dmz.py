import os
import requests
import sqlite3
import sys


def get_title_list(sqlite_path: str):
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()

    query = """
    SELECT
        I1.itemID as itemID,
        V1.value as title,
        I2.key as folder,
        V2.value
    FROM
        items as I1, items as I2, itemData as D1, itemData as D2, itemDataValues as V1, itemDataValues as V2, itemAttachments
    WHERE
        I1.itemTypeID != 3 and
        I1.itemID = D1.itemID and
        D1.valueID = V1.valueID and
        D1.fieldID = 1 and
        I1.itemID = itemAttachments.parentItemID and
        itemAttachments.contentType = "application/pdf" and
        I2.itemTypeID = 3 and
        I2.itemID = itemAttachments.itemID and
        itemAttachments.itemID = D2.itemID and 
        D2.fieldID = 1 and
        D2.valueID = V2.valueID
    ORDER BY
        I1.itemID
    """

    cursor.execute(query)
    result = cursor.fetchall()
    conn.close()

    return result


def get_attachment_list(sqlite_path: str):
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()

    query = """
    SELECT I.[key],
        IA.path,
        IDV.value
    FROM itemTypes AS IT,
        items AS I,
        itemAttachments AS IA,
        itemData AS ID,
        fields AS F,
        itemDataValues AS IDV
    WHERE IT.typeName = 'attachment' AND 
        F.fieldName = 'url' AND
        IT.itemTypeID = I.itemTypeID AND
        I.itemID = IA.itemID AND
        IA.itemID = ID.itemID AND
        ID.fieldID = F.fieldID AND
        ID.valueID = IDV.valueID
    ORDER BY I.itemID;
    """

    cursor.execute(query)
    result = cursor.fetchall()
    conn.close()

    return result


def convert_path(file_list: list, storage_path: str) -> list:
    result = []

    for dir, file, url in file_list:
        if dir == None or file == None or url == None:
            continue

        path = os.path.join(storage_path, dir, file.replace('storage:', ''))
        result.append([path, url])

    return result


def filter_file_not_exist(file_list: list) -> list:
    result = []

    for path, url in file_list:
        if not os.path.isfile(path):
            result.append([path, url])

    return result


def download_file(flie_list: list) -> list:

    for path, url in flie_list:
        try:
            response = requests.get(url)

            content_type = response.headers.get('Content-Type')
            if content_type == 'application/pdf':
                root_path = os.path.dirname(path)

                if not os.path.isdir(root_path):
                    os.makedirs(root_path)

                with open(path, 'wb') as file:
                    file.write(response.content)
                print(f'"{path}" from {url}')
            else:
                print(f'Error: cannot download "{path}" from {url}')    
        except:
            print(f'Error: while downloading "{path}" from {url}')


def download_missing_zotero(zotero_data_dir: str) -> None:
    print('Reading from', zotero_data_dir)

    sqlite_path = os.path.join(zotero_data_dir, 'zotero.sqlite')
    storage_path = os.path.join(zotero_data_dir, 'storage')

    result_all = get_attachment_list(sqlite_path)
    print('# of attachments =', len(result_all))

    result_all = convert_path(result_all, storage_path)

    result_filtered = filter_file_not_exist(result_all)
    print('# of attachments without file =', len(result_filtered))

    download_file(result_filtered)


if __name__ == '__main__':

    if len(sys.argv) < 2:
        print(f'Usage: python dmz.py <zotero_data_dir>')
    else:
        download_missing_zotero(sys.argv[1])
