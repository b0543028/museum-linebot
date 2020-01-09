using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;
using System.Web.Mvc;
using Newtonsoft.Json;
using Firebase.Database;
using Firebase.Database.Query;
using System.Threading.Tasks;
using MuseumLineBot.Models;

namespace MuseumLineBot.Controllers
{
    public class HomeController : Controller
    {
        public static string firebase_url = "https://museum-oitrbq.firebaseio.com/";
        //主頁
        public ActionResult Index()
        {
            return View();
        }

        //關於測試頁
        public async Task<ActionResult> About()
        {
            //Simulate test user data and login timestamp
            var userId = "12345";
            var currentLoginTime = DateTime.UtcNow.ToString("MM/dd/yyyy HH:mm:ss");

            //Save non identifying data to Firebase
            var currentUserLogin = new LoginData() { TimestampUtc = currentLoginTime };
            var firebaseClient = new FirebaseClient(firebase_url);
            var result = await firebaseClient
              .Child("Users/" + userId + "/Logins")
              .PostAsync(currentUserLogin);

            //Retrieve data from Firebase
            var dbLogins = await firebaseClient
              .Child("Users")
              .Child(userId)
              .Child("Logins")
              .OnceAsync<LoginData>();

            var timestampList = new List<DateTime>();

            //Convert JSON data to original datatype
            foreach (var login in dbLogins)
            {
                timestampList.Add(Convert.ToDateTime(login.Object.TimestampUtc).ToLocalTime());
            }

            //Pass data to the view
            ViewBag.CurrentUser = userId;
            ViewBag.Logins = timestampList.OrderByDescending(x => x);
            return View();
        }

        //資訊修改頁面
        public async Task<ActionResult> Museum()
        {
            //Simulate test user data and login timestamp
            var MuseumName = "LanyangMuseum";

            //Save non identifying data to Firebase
            //var currentUserLogin = new LoginData() { TimestampUtc = currentLoginTime };
            var firebaseClient = new FirebaseClient(firebase_url);
            //var result = await firebaseClient
            //  .Child("Users/" + userId + "/Logins")
            //  .PostAsync(currentUserLogin);

            //Retrieve data from Firebase
            var address = await firebaseClient
              .Child(MuseumName)
              .Child("Address")
              .OnceSingleAsync<AddressClass>();

            //Pass data to the view
            ViewBag.MuseumAddress = address.address;
            ViewBag.MuseumPhone = address.phone;
            return View();
        }

        //資訊上傳
        public async Task<ActionResult> UploadMuseum()
        {
            //Simulate test user data and login timestamp
            var MuseumName = "LanyangMuseum";

            //Save non identifying data to Firebase
            var firebaseClient = new FirebaseClient(firebase_url);
            UploadModel upload = new UploadModel();
            await Task.Run(() =>
            {
                upload.Update(Request["MuseumAddress"], Request["MuseumPhone"]);
            });

            //Retrieve data from Firebase
            var address = await firebaseClient
              .Child(MuseumName)
              .Child("Address")
              .OnceSingleAsync<AddressClass>();

            //Pass data to the view
            ViewBag.MuseumAddress = address.address;
            ViewBag.MuseumPhone = address.phone;
            return View("~/Views/Home/Museum.cshtml");
        }

        //問題回報頁面
        public async Task<ActionResult> Problem()
        {
            var MuseumName = "LanyangMuseum";
            var firebaseClient = new FirebaseClient(firebase_url);

            //取得資料
            try
            {
                var result_scan = await firebaseClient
                  .Child(MuseumName)
                  .Child("Help")
                  .OnceAsync<HelpClass>();

                var result_scan_solve = await firebaseClient
                  .Child(MuseumName)
                  .Child("Solve")
                  .OnceAsync<HelpClass>();

                ViewBag.data = result_scan.Select(m => m.Object.help);
                ViewBag.data1 = result_scan_solve.Select(m => m.Object.help);
            }
            catch
            {
                ViewBag.data = "目前沒有問題";
                ViewBag.data1 = "目前沒有解決的問題";
            }

            return View();
        }

        //問題上傳
        public async Task<ActionResult> UploadProblem()
        {
            var MuseumName = "LanyangMuseum";
            var firebaseClient = new FirebaseClient(firebase_url);

            //上傳資料
            var helpClass = new HelpClass() { help = Request["ProblemDescription"] };
            var result_post = await firebaseClient
              .Child(MuseumName + "/Help")
              .PostAsync(helpClass);

            //取得資料
            try
            {
                var result_scan = await firebaseClient
                  .Child(MuseumName)
                  .Child("Help")
                  .OnceAsync<HelpClass>();

                var result_scan_solve = await firebaseClient
                  .Child(MuseumName)
                  .Child("Solve")
                  .OnceAsync<HelpClass>();

                ViewBag.data = result_scan.Select(m => m.Object.help);
                ViewBag.data1 = result_scan_solve.Select(m => m.Object.help);
            }
            catch
            {
                ViewBag.data = "目前沒有問題";
                ViewBag.data1 = "目前沒有解決的問題";
            }

            return View("~/Views/Home/Problem.cshtml");
        }

        //刪除問題
        public async Task<ActionResult> DeleteProblem()
        {
            var MuseumName = "LanyangMuseum";
            var firebaseClient = new FirebaseClient(firebase_url);
            //刪除資料
            try
            {
                var result_scan = await firebaseClient
                  .Child(MuseumName)
                  .Child("Help")
                  .OnceAsync<HelpClass>();

                var result_data = result_scan.Where(m => m.Object.help.Equals(Request["Help"]));
                foreach (var item in result_data)
                {
                    await firebaseClient
                      .Child(MuseumName)
                      .Child("Help")
                      .Child(item.Key)
                      .DeleteAsync();
                }
            }
            catch
            {
                ViewBag.data = "無法刪除";
            }

            //取得資料
            try
            {
                var result_scan = await firebaseClient
                  .Child(MuseumName)
                  .Child("Help")
                  .OnceAsync<HelpClass>();

                var result_scan_solve = await firebaseClient
                  .Child(MuseumName)
                  .Child("Solve")
                  .OnceAsync<HelpClass>();

                ViewBag.data = result_scan.Select(m => m.Object.help);
                ViewBag.data1 = result_scan_solve.Select(m => m.Object.help);
            }
            catch
            {
                ViewBag.data = "目前沒有問題";
                ViewBag.data1 = "目前沒有解決的問題";
            }

            return View("~/Views/Home/Problem.cshtml");
        }

        //已解決問題，上傳到solve，並刪除問題
        public async Task<ActionResult> SolveProblem()
        {
            var MuseumName = "LanyangMuseum";
            var firebaseClient = new FirebaseClient(firebase_url);

            //上傳資料
            var helpClass = new HelpClass() { help = Request["Help"] };
            var result_post = await firebaseClient
              .Child(MuseumName + "/Solve")
              .PostAsync(helpClass);

            //刪除資料
            try
            {
                var result_scan = await firebaseClient
                  .Child(MuseumName)
                  .Child("Help")
                  .OnceAsync<HelpClass>();

                var result_data = result_scan.Where(m => m.Object.help.Equals(Request["Help"]));
                foreach (var item in result_data)
                {
                    await firebaseClient
                      .Child(MuseumName)
                      .Child("Help")
                      .Child(item.Key)
                      .DeleteAsync();
                }
            }
            catch
            {
                ViewBag.data = "無法刪除";
            }

            //取得資料
            try
            {
                var result_scan = await firebaseClient
                  .Child(MuseumName)
                  .Child("Help")
                  .OnceAsync<HelpClass>();

                var result_scan_solve = await firebaseClient
                  .Child(MuseumName)
                  .Child("Solve")
                  .OnceAsync<HelpClass>();

                ViewBag.data = result_scan.Select(m => m.Object.help);
                ViewBag.data1 = result_scan_solve.Select(m => m.Object.help);
            }
            catch
            {
                ViewBag.data = "目前沒有問題";
                ViewBag.data1 = "目前沒有解決的問題";
            }

            return View("~/Views/Home/Problem.cshtml");
        }

        //刪除已解決問題
        public async Task<ActionResult> DeleteSolveProblem()
        {
            var MuseumName = "LanyangMuseum";
            var firebaseClient = new FirebaseClient(firebase_url);
            //刪除資料
            try
            {
                var result_scan = await firebaseClient
                  .Child(MuseumName)
                  .Child("Solve")
                  .OnceAsync<HelpClass>();

                var result_data = result_scan.Where(m => m.Object.help.Equals(Request["Help"]));
                foreach (var item in result_data)
                {
                    await firebaseClient
                      .Child(MuseumName)
                      .Child("Solve")
                      .Child(item.Key)
                      .DeleteAsync();
                }
            }
            catch
            {
                ViewBag.data = "無法刪除";
            }

            //取得資料
            try
            {
                var result_scan = await firebaseClient
                  .Child(MuseumName)
                  .Child("Help")
                  .OnceAsync<HelpClass>();

                var result_scan_solve = await firebaseClient
                  .Child(MuseumName)
                  .Child("Solve")
                  .OnceAsync<HelpClass>();

                ViewBag.data = result_scan.Select(m => m.Object.help);
                ViewBag.data1 = result_scan_solve.Select(m => m.Object.help);
            }
            catch
            {
                ViewBag.data = "目前沒有問題";
                ViewBag.data1 = "目前沒有解決的問題";
            }

            return View("~/Views/Home/Problem.cshtml");
        }
    }
}
 