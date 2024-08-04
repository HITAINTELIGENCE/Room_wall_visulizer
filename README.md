# HIT ROOM 

## Giới thiệu


## Chức năng chính


## 👩‍💻 Tổng Quan Hệ Thống

Backend của hệ thống được thiết kế với các công nghệ sử dụng như sau:

-   [FastAPI](https://fastapi.tiangolo.com/): Dựng API cho PSPNet Service.
-   [Nginx](https://nginx.org/en/): Web server cho Nginx.
-   [Docker](https://www.docker.com/): Containerize các service.
-   [Docker Compose](https://docs.docker.com/compose/): Quản lý các container.

## Hướng Dẫn Cài Đặt

Tất cả các images build từ services backend bạn có thể tìm thấy tại [Docker Hub](https://hub.docker.com/repository/docker/hungmanhhoang/room-visualizer-app/general).


### Yêu Cầu 📋

Để cài đặt và chạy được dự án, trước tiên bạn cần phải cài đặt các công cụ bên dưới. Hãy thực hiện theo các hướng dẫn cài đặt sau, lưu ý chọn hệ điều hành phù hợp với máy tính của bạn:

-   [Docker-Installation](https://docs.docker.com/get-docker/)
-   [Docker-Compose-Installation](https://docs.docker.com/compose/install/)

### 🔨 Cài Đặt

Trước hết, hãy clone dự án về máy tính của bạn:

```bash
git clone https://github.com/HITAINTELIGENCE/Room_wall_visulizer
```

cd vào thư mục Room_wall_visulizer:

```bash
cd Room_wall_visulizer
```

### Chạy hệ thống
-   Start các services với 1 lệnh docker-compose:

```bash
docker-compose -f docker-compose-production.yaml up -d
```

#### PORT BINDING

-   Sau khi chạy xong, các service sẽ được chạy trên các port như sau:
<table width="100%">
    <thead>
        <th>Service</th>
        <th>PORT</th>
    </thead>

<tbody>
<tr>
<td>API Gateway</td>
<td>

8000:8000

8001:8001

8002:8002

8003:8003

8004:8004

</td>

</tr>
<tr>
<td>Auth Service</td>
<td>5000:5000</td>
</tr>
<tr>
<td>Law Service</td>
<td>8080:8080</td>
</tr>
<tr>
<td>RAG Service</td>
<td>5001:5001</td>
</tr>
<tr>
<td>Recommendation Service</td>
<td>5002:5002</td>
</tr>
</tbody>
</table>