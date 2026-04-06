import ws from "k6/ws";
import { check } from "k6";

export const options = {
  vus: 20,
  duration: "1m",
};

export default function () {
  const url = "ws://localhost:8000/api/v1/streams/live";
  const res = ws.connect(url, {}, function (socket) {
    socket.on("message", function () {
      socket.close();
    });
    socket.setTimeout(function () {
      socket.close();
    }, 1500);
  });

  check(res, { "ws upgraded": (r) => r && r.status === 101 });
}
