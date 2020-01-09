using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

using FireSharp.Config;
using FireSharp.Interfaces;
using FireSharp.Response;

using Firebase.Database;
using Firebase.Database.Query;

namespace MuseumLineBot.Models
{
    public class UploadModel
    {
        IFirebaseConfig config = new FirebaseConfig
        {
            AuthSecret = "fKxPU1TRBefUOHPIXOvHtkiCKLYH6XKsaZz1vKFB",
            BasePath = "https://museum-oitrbq.firebaseio.com/"
        };

        IFirebaseClient Client;

        public async void Update(string address, string phone)
        {
            Client = new FireSharp.FirebaseClient(config);

            var Addressdata = new AddressClass
            {
                address = address,
                phone = phone
            };

            FirebaseResponse response = await Client.UpdateTaskAsync("LanyangMuseum/Address", Addressdata);
        }

        public async void HelpUpdate(string help)
        {
            var MuseumName = "LanyangMuseum";

            var helpClass = new HelpClass() { help = help };
            var firebaseClient = new FirebaseClient("https://museum-oitrbq.firebaseio.com/");
            var result = await firebaseClient
              .Child(MuseumName + "/Help")
              .PostAsync(helpClass);
        }
    }
}